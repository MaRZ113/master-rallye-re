import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Instruction;
import ghidra.program.model.listing.InstructionIterator;
import ghidra.program.model.listing.Function;
import ghidra.program.model.symbol.Reference;
import ghidra.program.model.symbol.ReferenceIterator;
import java.io.BufferedWriter;
import java.io.ByteArrayOutputStream;
import java.io.FileWriter;
import java.io.PrintWriter;
import java.nio.charset.StandardCharsets;
import java.util.LinkedHashMap;
import java.util.Map;

/** Dump direct string references and containing functions for Results identity. */
public class DumpVehicleRaceResults extends GhidraScript {
    private final Map<String, Function> functions = new LinkedHashMap<>();

    @Override
    protected void run() throws Exception {
        String[] args = getScriptArgs();
        if (args.length != 1) {
            throw new IllegalArgumentException("usage: DumpVehicleRaceResults.java <output.txt>");
        }
        try (PrintWriter out = new PrintWriter(new BufferedWriter(new FileWriter(args[0])))) {
            out.println("PROGRAM=" + currentProgram.getName());
            String[] terms = {
                "Frontend/RaceResults/NameList",
                "Frontend/RaceResults/PositionList",
                "Frontend/RaceResults/TimeList",
                "Frontend/RaceResults/Car0",
                "RaceData/Competitor0/CarID",
                "RaceData/Competitor0/DriverID",
                "GALOCAL UNKNOWN"
            };
            for (String term : terms) {
                dumpTerm(out, term);
            }
            String[] targets = {
                "0047C840", "0047D340", "0047D400", "0047D6D0", "0047D7E0",
                "0047D8D0", "0047D9D0", "0047C6C0", "004AC7B0",
                "004AC660", "004AC7F0", "004AC770", "00458980",
                "00485AA0", "00485B80",
                "00485BF0", "00485C20", "00485CA0"
            };
            for (String target : targets) {
                dumpFunctionTarget(out, target);
            }
            dumpRange(out, "00601FE0", "00602060");
            dumpRange(out, "00602130", "006021A0");
            dumpLocalizationGroup(out, "default", "006c9a60", 0x39);
            dumpLocalizationGroup(out, "language-1", "006bb888", 0x39);
            dumpLocalizationGroup(out, "language-2", "006b8000", 0x39);
            dumpLocalizationGroup(out, "language-3", "006c2998", 0x39);
            dumpLocalizationGroup(out, "language-4", "006bf110", 0x39);
            dumpLocalizationGroup(out, "language-5", "006c6220", 0x39);
            DecompInterface decompiler = new DecompInterface();
            try {
                decompiler.openProgram(currentProgram);
                for (Function function : functions.values()) {
                    out.println("\nFUNCTION " + function.getEntryPoint() + " " + function.getName());
                    DecompileResults result = decompiler.decompileFunction(function, 120, monitor);
                    if (result != null && result.decompileCompleted()) {
                        out.println(result.getDecompiledFunction().getC());
                    } else {
                        out.println("<decompile failed: " + (result == null ? "null" : result.getErrorMessage()) + ">");
                    }
                }
            } finally {
                decompiler.dispose();
            }
        }
    }

    private void dumpRange(PrintWriter out, String startText, String endText) throws Exception {
        Address start = toAddr(startText);
        Address end = toAddr(endText);
        out.println("\nRANGE " + start + ".." + end);
        InstructionIterator instructions = currentProgram.getListing().getInstructions(
            new ghidra.program.model.address.AddressSet(start, end), true);
        while (instructions.hasNext()) {
            Instruction instruction = instructions.next();
            if (instruction.getAddress().compareTo(end) > 0) {
                break;
            }
            StringBuilder bytes = new StringBuilder();
            for (byte value : instruction.getBytes()) {
                bytes.append(String.format("%02X", value & 0xff));
            }
            out.println("INSN " + instruction.getAddress() + " " + instruction + " bytes=" + bytes);
        }
    }

    private void dumpFunctionTarget(PrintWriter out, String addressText) throws Exception {
        Address address = toAddr(addressText);
        Function target = currentProgram.getFunctionManager().getFunctionAt(address);
        out.println("\nTARGET " + address + " function=" + target);
        if (target != null) {
            functions.put(target.getEntryPoint().toString(), target);
            if (address.getOffset() == 0x0047C840L) {
                InstructionIterator instructions = currentProgram.getListing().getInstructions(target.getBody(), true);
                while (instructions.hasNext()) {
                    Instruction instruction = instructions.next();
                    StringBuilder bytes = new StringBuilder();
                    for (byte value : instruction.getBytes()) {
                        bytes.append(String.format("%02X", value & 0xff));
                    }
                    out.println("INSN " + instruction.getAddress() + " " + instruction + " bytes=" + bytes);
                }
            }
        }
        ReferenceIterator refs = currentProgram.getReferenceManager().getReferencesTo(address);
        while (refs.hasNext()) {
            Reference ref = refs.next();
            Function caller = currentProgram.getFunctionManager().getFunctionContaining(ref.getFromAddress());
            out.println("CALLREF from=" + ref.getFromAddress() + " type=" + ref.getReferenceType()
                + " caller=" + (caller == null ? "<none>" : caller.getEntryPoint() + " " + caller.getName()));
            if (caller != null) {
                functions.put(caller.getEntryPoint().toString(), caller);
            }
        }
    }

    private void dumpLocalizationGroup(PrintWriter out, String label, String baseText, int wantedGroup)
            throws Exception {
        Address row = toAddr(baseText);
        out.println("\nLOCALIZATION_TABLE " + label + " base=" + row + " group=" + wantedGroup);
        for (int i = 0; i < 10000; i++, row = row.add(12)) {
            int group = currentProgram.getMemory().getInt(row);
            if (group == -2) {
                out.println("SENTINEL index=" + i);
                return;
            }
            if (group != wantedGroup) {
                continue;
            }
            int selector = currentProgram.getMemory().getInt(row.add(4));
            int stringAddress = currentProgram.getMemory().getInt(row.add(8));
            String value = readString(toAddr(Integer.toUnsignedLong(stringAddress)));
            out.println("ROW index=" + i + " selector=" + selector + " text=" + value);
        }
        out.println("TABLE_LIMIT_REACHED");
    }

    private String readString(Address address) throws Exception {
        ByteArrayOutputStream bytes = new ByteArrayOutputStream();
        for (int i = 0; i < 4096; i++) {
            byte value = currentProgram.getMemory().getByte(address.add(i));
            if (value == 0) {
                return new String(bytes.toByteArray(), StandardCharsets.UTF_8);
            }
            bytes.write(value);
        }
        return "<unterminated@" + address + ">";
    }

    private void dumpTerm(PrintWriter out, String term) throws Exception {
        Address address = currentProgram.getMemory().findBytes(
            currentProgram.getMinAddress(), currentProgram.getMaxAddress(),
            term.getBytes(StandardCharsets.US_ASCII), null, true, monitor);
        out.println("\nTERM " + term + " address=" + address);
        if (address == null) {
            return;
        }
        ReferenceIterator refs = currentProgram.getReferenceManager().getReferencesTo(address);
        while (refs.hasNext()) {
            Reference ref = refs.next();
            Function function = currentProgram.getFunctionManager().getFunctionContaining(ref.getFromAddress());
            out.println("REF from=" + ref.getFromAddress() + " type=" + ref.getReferenceType()
                + " function=" + (function == null ? "<none>" : function.getEntryPoint() + " " + function.getName()));
            if (function != null) {
                functions.put(function.getEntryPoint().toString(), function);
            }
        }
    }
}
