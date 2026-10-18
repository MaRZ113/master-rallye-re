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

/**
 * Read-only: for each hex address argument, decompile the containing function, list its calls and its callers.
 * Args: output path, then addresses (0x...). Run against the canonical ELF (r5900:LE:32:default).
 */
public class DecompFns extends ghidra.app.script.GhidraScript {
    private BufferedWriter out;

    private void line(String s) throws Exception { out.write(s); out.newLine(); }

    @Override
    protected void run() throws Exception {
        String[] args = getScriptArgs();
        if (args.length < 2) throw new IllegalArgumentException("output path and at least one address");
        if (!"r5900:LE:32:default".equals(currentProgram.getLanguage().getLanguageID().toString()))
            throw new IllegalStateException("Wrong language");
        Path output = Paths.get(args[0]);
        Files.createDirectories(output.getParent());
        out = Files.newBufferedWriter(output, StandardCharsets.UTF_8);
        DecompInterface decompiler = new DecompInterface();
        decompiler.openProgram(currentProgram);
        try {
            for (int i = 1; i < args.length; i++) {
                long va = Long.decode(args[i]);
                Address a = toAddr(va);
                Function f = currentProgram.getFunctionManager().getFunctionContaining(a);
                if (f == null) { line("NO_FUNCTION\t" + args[i]); continue; }
                line("FUNCTION\t" + f.getEntryPoint() + ".." + f.getBody().getMaxAddress() + "\tbytes=" + f.getBody().getNumAddresses());
                for (Reference r : getReferencesTo(f.getEntryPoint())) {
                    Function c = currentProgram.getFunctionManager().getFunctionContaining(r.getFromAddress());
                    line("CALLER\t" + r.getFromAddress() + "\t" + (c == null ? "UNDEFINED" : c.getEntryPoint().toString()));
                }
                for (Instruction ins : currentProgram.getListing().getInstructions(f.getBody(), true)) {
                    if (ins.getFlowType().isCall()) {
                        StringBuilder d = new StringBuilder();
                        for (Address fl : ins.getFlows()) d.append(fl).append(' ');
                        line("CALL\t" + ins.getAddress() + "\t" + d);
                    }
                }
                if (f.getBody().getNumAddresses() > 0x4000) { line("DECOMP_SKIPPED_LARGE"); continue; }
                DecompileResults res = decompiler.decompileFunction(f, 60, monitor);
                line("DECOMP_BEGIN\tcomplete=" + res.decompileCompleted());
                if (res.getDecompiledFunction() != null)
                    for (String s : res.getDecompiledFunction().getC().split("\r?\n")) line("C\t" + s);
                line("DECOMP_END");
            }
        } finally {
            decompiler.dispose();
            out.close();
        }
    }
}
