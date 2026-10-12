import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.Instruction;
import ghidra.program.model.symbol.Reference;
import java.io.BufferedWriter;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Set;

/**
 * Bounded, read-only Ghidra headless probe for the original R5900 foliage path.
 * Run only against the canonical ELF imported with r5900:LE:32:default.
 */
public class EERevalidation2 extends ghidra.app.script.GhidraScript {
    private static final long[][] TARGETS = {
        {0x00390d98L, 0x00390f50L}, // shader token extraction
        {0x00391690L, 0x00391d34L}, // material resolution
        {0x003a6c58L, 0x003a6ea4L}, // shader registry dispatch
        {0x003a7468L, 0x003a74d4L}, // treeblend registration
        {0x003a75b8L, 0x003a7624L}, // tree registration
        {0x003ae618L, 0x003ae66cL}, // treeblend material callback
        {0x003ae710L, 0x003ae75cL}, // tree material callback
        {0x003ae760L, 0x003ae7acL}, // ordinary object callback
        {0x00312610L, 0x00316800L}, // shared mode / GS producer
        {0x00340ce0L, 0x00340f40L}, // shared GS state template initialization
        {0x0031af50L, 0x0031b1ecL}, // VU selector upload
        {0x0031d0d8L, 0x0031d108L}, // queue drain bucket advancement
        {0x0031c8f8L, 0x0031cd94L}, // renderer context / indirect dispatch owner
        {0x0031cd98L, 0x0031d1b0L}, // render queue drain
        {0x0031d250L, 0x0031d794L}, // bucket/material enqueue
        {0x0032ff20L, 0x0032ff60L}, // first direct caller route to renderer dispatch
        {0x003301c8L, 0x00330200L}, // second direct caller route to renderer dispatch
        {0x003302e0L, 0x00330310L}, // renderer dispatch to draw-owner call
        {0x00330c80L, 0x00330d40L}, // generic caller of renderer drain vtable slot
        {0x0031c438L, 0x0031c520L}, // dirty-state commit / producer callsites
        {0x003bca80L, 0x003bcbb4L}, // mesh draw callback
        {0x003a7f40L, 0x003a7facL}, // source RGBA unpack
        {0x003401f0L, 0x00340230L}, // channel clamp
        {0x0031f844L, 0x0031f9b0L}, // cache source color scale, all RGBA channels
        {0x00341198L, 0x003412ecL}  // GS register identity helper and table setup
    };

    private static final long[] XREF_TARGETS = {
        0x004875e0L, 0x00487610L, 0x00487d7cL, 0x00487d1cL,
        0x00487cfcL, 0x00488384L, 0x004850c0L, 0x004853f0L,
        0x004854a4L, 0x004854acL, 0x0042de10L, 0x0042df10L,
        0x0032ff28L, 0x003301c8L, 0x003302b8L,
        0x00330d00L, 0x00330780L, 0x0031cd98L,
        0x0031f4e0L, 0x003a7f10L, 0x003401f0L,
        0x0042dea0L, 0x0042deb0L, 0x00312610L,
        0x0031c438L, 0x003bca80L, 0x0031af50L
    };

    private static final long[] DECOMPILE_TARGETS = {
        0x003ae618L, 0x003ae710L, 0x0031cd98L, 0x0031d250L,
        0x0031f4e0L, 0x0032ff28L, 0x003301c8L, 0x003302b8L,
        0x003a7f10L, 0x003401f0L
    };

    private static final long[] FLOW_TARGETS = {
        0x0031cd98L, 0x0031d250L, 0x0032ff28L, 0x003301c8L,
        0x003302b8L, 0x00330780L
    };

    private BufferedWriter out;
    private final Set<String> emittedInstructions = new HashSet<>();

    private void line(String value) throws Exception {
        out.write(value);
        out.newLine();
    }

    private String bytes(byte[] value) {
        StringBuilder b = new StringBuilder(value.length * 2);
        for (byte v : value) b.append(String.format("%02x", v & 0xff));
        return b.toString();
    }

    private void dumpRange(long startVa, long endVa) throws Exception {
        Address cursor = toAddr(startVa);
        Address end = toAddr(endVa);
        int holes = 0;
        while (cursor.compareTo(end) <= 0 && !monitor.isCancelled()) {
            Instruction instruction = currentProgram.getListing().getInstructionAt(cursor);
            if (instruction == null) {
                holes++;
                cursor = cursor.add(4);
                continue;
            }
            String key = instruction.getAddress().toString();
            if (emittedInstructions.add(key)) {
                line("INS\t" + instruction.getAddress() + "\t" + bytes(instruction.getBytes()) +
                    "\t" + instruction.toString());
            }
            cursor = instruction.getAddress().add(instruction.getLength());
        }
        line("RANGE_END\t" + String.format("0x%08x..0x%08x", startVa, endVa) + "\tholes=" + holes);
    }

    private void dumpReferences(long va) throws Exception {
        Address target = toAddr(va);
        FunctionManagerDump(target);
        Reference[] refs = getReferencesTo(target);
        int count = 0;
        for (Reference ref : refs) {
            if (count++ >= 500) break;
            Function caller = currentProgram.getFunctionManager().getFunctionContaining(ref.getFromAddress());
            String owner = caller == null ? "UNDEFINED" :
                caller.getName() + "@" + caller.getEntryPoint();
            line("XREF\t" + target + "\tfrom=" + ref.getFromAddress() + "\ttype=" +
                ref.getReferenceType() + "\towner=" + owner);
        }
        if (count >= 500) line("XREF_TRUNCATED\t" + target);
    }

    private void FunctionManagerDump(Address address) throws Exception {
        Function function = currentProgram.getFunctionManager().getFunctionAt(address);
        if (function == null) function = currentProgram.getFunctionManager().getFunctionContaining(address);
        if (function == null) {
            line("TARGET_FUNCTION\t" + address + "\tUNDEFINED");
        } else {
            line("TARGET_FUNCTION\t" + address + "\t" + function.getEntryPoint() + ".." +
                function.getBody().getMaxAddress() + "\t" + function.getName() + "\tbytes=" +
                function.getBody().getNumAddresses());
        }
    }

    private void dumpCallersAndAncestors(long targetVa) throws Exception {
        Address root = toAddr(targetVa);
        ArrayDeque<Address> queue = new ArrayDeque<>();
        Set<String> seen = new LinkedHashSet<>();
        queue.add(root);
        int depth = 0;
        while (!queue.isEmpty() && seen.size() < 120 && depth < 5) {
            int atDepth = queue.size();
            for (int i = 0; i < atDepth && seen.size() < 120; i++) {
                Address callee = queue.removeFirst();
                Function calleeFunction = currentProgram.getFunctionManager().getFunctionAt(callee);
                if (calleeFunction == null) calleeFunction = currentProgram.getFunctionManager().getFunctionContaining(callee);
                Address entry = calleeFunction == null ? callee : calleeFunction.getEntryPoint();
                if (!seen.add(entry.toString())) continue;
                Reference[] refs = getReferencesTo(entry);
                int fanout = 0;
                for (Reference ref : refs) {
                    if (fanout >= 80 || seen.size() >= 120) break;
                    if (!ref.getReferenceType().isCall()) continue;
                    fanout++;
                    Function caller = currentProgram.getFunctionManager().getFunctionContaining(ref.getFromAddress());
                    if (caller == null) {
                        line("CALLER\tdepth=" + depth + "\tcallee=" + entry + "\tsite=" +
                            ref.getFromAddress() + "\towner=UNDEFINED");
                    } else {
                        line("CALLER\tdepth=" + depth + "\tcallee=" + entry + "\tsite=" +
                            ref.getFromAddress() + "\tcaller=" + caller.getEntryPoint() +
                            "\t" + caller.getName());
                        if (depth < 4) queue.addLast(caller.getEntryPoint());
                    }
                }
                if (fanout >= 80) line("CALLER_FANOUT_TRUNCATED\t" + entry);
            }
            depth++;
        }
        if (!queue.isEmpty()) line("CALLER_ANCESTRY_TRUNCATED\tremaining=" + queue.size());
    }

    private void dumpDecompile(long targetVa) throws Exception {
        Function function = currentProgram.getFunctionManager().getFunctionAt(toAddr(targetVa));
        if (function == null) {
            line("DECOMP\t" + String.format("0x%08x", targetVa) + "\tNO_FUNCTION");
            return;
        }
        if (function.getBody().getNumAddresses() > 0x2000) {
            line("DECOMP\t" + function.getEntryPoint() + "\tSKIPPED_LARGE\tbytes=" +
                function.getBody().getNumAddresses());
            return;
        }
        DecompInterface decompiler = new DecompInterface();
        decompiler.openProgram(currentProgram);
        DecompileResults result = decompiler.decompileFunction(function, 30, monitor);
        line("DECOMP_BEGIN\t" + function.getEntryPoint() + ".." +
            function.getBody().getMaxAddress() + "\tcomplete=" + result.decompileCompleted());
        if (result.getErrorMessage() != null && !result.getErrorMessage().isEmpty()) {
            line("DECOMP_ERROR\t" + result.getErrorMessage().replace('\n', ' '));
        }
        if (result.getDecompiledFunction() != null) {
            for (String sourceLine : result.getDecompiledFunction().getC().split("\\R")) {
                line("C\t" + sourceLine);
            }
        }
        line("DECOMP_END\t" + function.getEntryPoint());
        decompiler.dispose();
    }

    private void dumpFlowSummary(long targetVa) throws Exception {
        Function function = currentProgram.getFunctionManager().getFunctionAt(toAddr(targetVa));
        if (function == null) {
            line("FLOW_FUNCTION_BEGIN\t" + String.format("0x%08x", targetVa) + "\tNO_FUNCTION");
            return;
        }
        line("FLOW_FUNCTION_BEGIN\t" + function.getEntryPoint() + ".." +
            function.getBody().getMaxAddress());
        int calls = 0;
        int backwardBranches = 0;
        for (Instruction instruction : currentProgram.getListing().getInstructions(function.getBody(), true)) {
            Address[] flows = instruction.getFlows();
            if (instruction.getFlowType().isCall()) {
                calls++;
                StringBuilder destinations = new StringBuilder();
                for (Address flow : flows) {
                    if (destinations.length() != 0) destinations.append(',');
                    destinations.append(flow);
                }
                line("FLOW_CALL\towner=" + function.getEntryPoint() + "\tsite=" +
                    instruction.getAddress() + "\t" + bytes(instruction.getBytes()) +
                    "\t" + instruction + "\tto=" + destinations);
            } else if (instruction.getFlowType().isConditional() || instruction.getFlowType().isJump()) {
                for (Address flow : flows) {
                    if (flow.compareTo(instruction.getAddress()) < 0) {
                        backwardBranches++;
                        line("FLOW_BACKEDGE\towner=" + function.getEntryPoint() +
                            "\tsite=" + instruction.getAddress() + "\t" +
                            bytes(instruction.getBytes()) + "\t" + instruction + "\tto=" + flow);
                    }
                }
            }
        }
        line("FLOW_SUMMARY\t" + function.getEntryPoint() + ".." +
            function.getBody().getMaxAddress() + "\tcalls=" + calls +
            "\tbackward_branches=" + backwardBranches);
    }

    @Override
    protected void run() throws Exception {
        String[] args = getScriptArgs();
        if (args.length != 1) throw new IllegalArgumentException("Expected one absolute output path");
        if (!"r5900:LE:32:default".equals(currentProgram.getLanguage().getLanguageID().toString())) {
            throw new IllegalStateException("Wrong language: " + currentProgram.getLanguage().getLanguageID());
        }
        Path output = Paths.get(args[0]);
        Files.createDirectories(output.getParent());
        out = Files.newBufferedWriter(output, StandardCharsets.UTF_8);
        try {
            line("PROGRAM\t" + currentProgram.getName());
            line("LANGUAGE\t" + currentProgram.getLanguage().getLanguageID());
            line("COMPILER\t" + currentProgram.getCompilerSpec().getCompilerSpecID());
            line("BYTE_ORDER\t" + (currentProgram.getLanguage().isBigEndian() ? "BE" : "LE"));
            line("IMAGE_BASE\t" + currentProgram.getImageBase());
            line("SOURCE_NOTE\tVerify ELF SHA and source bytes with companion verifier");
            for (long[] target : TARGETS) {
                Function function = currentProgram.getFunctionManager().getFunctionAt(toAddr(target[0]));
                if (function == null) function = currentProgram.getFunctionManager().getFunctionContaining(toAddr(target[0]));
                line("TARGET\t" + String.format("0x%08x..0x%08x", target[0], target[1]) +
                    "\tfunction=" + (function == null ? "UNDEFINED" :
                    function.getName() + "@" + function.getEntryPoint() + ".." + function.getBody().getMaxAddress()));
                dumpRange(target[0], target[1]);
            }
            for (long va : XREF_TARGETS) dumpReferences(va);
            line("DECOMPILE_BEGIN_GROUP");
            for (long va : DECOMPILE_TARGETS) dumpDecompile(va);
            line("DECOMPILE_END_GROUP");
            line("FLOW_BEGIN_GROUP");
            for (long va : FLOW_TARGETS) dumpFlowSummary(va);
            line("FLOW_END_GROUP");
            line("CALL_GRAPH_BEGIN\tqueue_drain=0x0031cd98");
            dumpCallersAndAncestors(0x0031cd98L);
            line("CALL_GRAPH_END");
            line("CALL_GRAPH_BEGIN\tmesh_dispatch_owner=0x00330780");
            dumpCallersAndAncestors(0x00330780L);
            line("CALL_GRAPH_END");
            line("CALL_GRAPH_BEGIN\tdispatcher=0x003302b8");
            dumpCallersAndAncestors(0x003302b8L);
            line("CALL_GRAPH_END");
            line("CALL_GRAPH_BEGIN\tfirst_route=0x0032ff28");
            dumpCallersAndAncestors(0x0032ff28L);
            line("CALL_GRAPH_END");
            line("CALL_GRAPH_BEGIN\tsecond_route=0x003301c8");
            dumpCallersAndAncestors(0x003301c8L);
            line("CALL_GRAPH_END");
            line("END");
            out.flush();
            println("Wrote bounded R5900 revalidation evidence: " + output);
        } finally {
            out.close();
        }
    }
}
