// Focused retail analysis for the R-PHYS2.1 named-family source question.
// Arguments: <output-text>
import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Data;
import ghidra.program.model.listing.DataIterator;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.Instruction;
import ghidra.program.model.listing.InstructionIterator;
import ghidra.program.model.symbol.Reference;
import ghidra.program.model.symbol.ReferenceIterator;
import java.io.FileWriter;
import java.io.PrintWriter;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;

public class RPhys21NamedFamilyAudit extends GhidraScript {
    private static final String[] TARGETS = {
        "0044a320", "00449d40", "0044fa80", "0044ed50", "0044e400", "004b0630", "004ac660",
        "0045a3c0", "00458cd0", "00458af0", "00458d60", "00458da0",
        "00458e70", "004598d0", "0045a0b0", "004b0af0", "004b03a0", "004b0490",
        "004b0670", "004b0700", "004b0750", "004b0790", "004b0820",
        "004abbd0", "004ac590", "004ac610", "004ac930", "004ada50",
        "0044a450", "0044a510", "0044a710", "004d1990", "004d11d0", "004d15c0", "004d1240",
        "004d8ec0", "004d6760", "004d0580", "005d3ad6", "004ac040", "004ac070",
        "004400a0", "0040f600", "0040f740", "0040f720", "005d3b03",
        "00493770", "00493e30", "00493fd0", "00493600", "004938c0",
        "0049b0c0", "0049b940", "0049c950", "0049cef0", "0049e970", "004a01d0",
        "004a1a30", "004a32f0", "004940a0", "00494730", "00495460", "004958e0",
        "00496d20", "00498090", "00499400", "0049a800"
    };

    private Function findFunction(String addressText) {
        Address address = toAddr(Long.parseLong(addressText, 16));
        Function function = currentProgram.getFunctionManager().getFunctionAt(address);
        return function == null ? currentProgram.getFunctionManager().getFunctionContaining(address) : function;
    }

    private void printReferences(PrintWriter out, Function function) {
        out.println("CALLERS:");
        ReferenceIterator refs = currentProgram.getReferenceManager().getReferencesTo(function.getEntryPoint());
        while (refs.hasNext()) {
            Reference reference = refs.next();
            Function caller = currentProgram.getFunctionManager().getFunctionContaining(reference.getFromAddress());
            out.println("  " + reference.getFromAddress() + " " + reference.getReferenceType() +
                " caller=" + (caller == null ? "UNKNOWN" : caller.getName() + "@" + caller.getEntryPoint()));
        }
    }

    private void printFunction(PrintWriter out, String addressText, DecompInterface decompiler) {
        out.println("\n===== FUNCTION TARGET 0x" + addressText + " =====");
        Function function = findFunction(addressText);
        if (function == null) {
            out.println("NO_FUNCTION");
            return;
        }
        out.println("FUNCTION " + function.getName() + " ENTRY " + function.getEntryPoint());
        DecompileResults result = decompiler.decompileFunction(function, 180, monitor);
        if (result != null && result.decompileCompleted() && result.getDecompiledFunction() != null) {
            out.println(result.getDecompiledFunction().getC());
        } else {
            out.println("DECOMPILE_FAILED " + (result == null ? "null" : result.getErrorMessage()));
        }
        printReferences(out, function);
    }

    private void printInstructions(PrintWriter out, String addressText) throws Exception {
        out.println("\n===== INSTRUCTIONS TARGET 0x" + addressText + " =====");
        Function function = findFunction(addressText);
        if (function == null) {
            out.println("NO_FUNCTION");
            return;
        }
        InstructionIterator iterator = currentProgram.getListing().getInstructions(function.getBody(), true);
        while (iterator.hasNext()) {
            monitor.checkCancelled();
            Instruction instruction = iterator.next();
            out.println(instruction.getAddress() + "  " + instruction);
            for (var pcode : instruction.getPcode()) {
                out.println("    pcode: " + pcode);
            }
        }
    }

    private void printRelevantStrings(PrintWriter out) throws Exception {
        out.println("\n===== RELEVANT STRINGS =====");
        List<Data> matches = new ArrayList<>();
        DataIterator iterator = currentProgram.getListing().getDefinedData(true);
        while (iterator.hasNext()) {
            monitor.checkCancelled();
            Data data = iterator.next();
            Object value = data.getValue();
            if (!(value instanceof String)) continue;
            String lower = ((String)value).toLowerCase(Locale.ROOT);
            if (lower.equals("vehicles/") || lower.equals("vehicles/car") ||
                lower.contains("navara") || lower.equals("jump") || lower.contains("trooper") ||
                lower.contains("forklift") || lower.contains("player1") ||
                lower.contains("player2") || lower.equals("landcruiser") ||
                lower.equals("pajero") || lower.equals("tata") || lower.equals("terrano") ||
                lower.equals("chevyblazer") || lower.equals("xtrail") || lower.equals("frontera") ||
                lower.equals("forester") || lower.equals("rmonster") || lower.equals("patrol") ||
                lower.equals("newrav") || lower.equals("kiasportage") || lower.equals("wildcat") ||
                lower.equals("simmbugghini") || lower.equals("astero") || lower.equals("kangoo") ||
                lower.equals("megane") || lower.equals("mattserati") || lower.equals("bruno") ||
                lower.equals("seatbuggy") || lower.equals("kamaz") || lower.equals("icecream") ||
                lower.equals("ufo")) {
                matches.add(data);
            }
        }
        for (Data data : matches) {
            out.println("STRING " + data.getAddress() + " " + data.getValue());
            ReferenceIterator refs = currentProgram.getReferenceManager().getReferencesTo(data.getAddress());
            while (refs.hasNext()) {
                Reference reference = refs.next();
                Function function = currentProgram.getFunctionManager().getFunctionContaining(reference.getFromAddress());
                out.println("  XREF " + reference.getFromAddress() + " " + reference.getReferenceType() +
                    " function=" + (function == null ? "UNKNOWN" : function.getName() + "@" + function.getEntryPoint()));
            }
        }
    }

    private void printRawFamilyStrings(PrintWriter out) {
        out.println("\n===== RAW FAMILY STRING BYTES =====");
        String[] addresses = {"006b3d40", "006b3cfc", "006b3c6c"};
        for (String addressText : addresses) {
            Address address = toAddr(Long.parseLong(addressText, 16));
            StringBuilder value = new StringBuilder();
            try {
                for (int offset = 0; offset < 64; offset++) {
                    int character = currentProgram.getMemory().getByte(address.add(offset)) & 0xff;
                    if (character == 0) break;
                    if (character < 0x20 || character > 0x7e) {
                        value.append("<non-ascii>");
                        break;
                    }
                    value.append((char)character);
                }
                out.println("RAW_FAMILY_STRING " + address + " " + value);
            } catch (Exception exception) {
                out.println("RAW_FAMILY_STRING " + address + " READ_FAILED " + exception.getMessage());
            }
        }
    }

    @Override
    public void run() throws Exception {
        if (getScriptArgs().length != 1) {
            printerr("Expected one argument: output path");
            return;
        }
        DecompInterface decompiler = new DecompInterface();
        decompiler.openProgram(currentProgram);
        try (PrintWriter out = new PrintWriter(new FileWriter(getScriptArgs()[0], false))) {
            out.println("PROGRAM " + currentProgram.getName());
            out.println("IMAGE_BASE " + currentProgram.getImageBase());
            for (String target : TARGETS) printFunction(out, target, decompiler);
            printInstructions(out, "0044ed50");
            printInstructions(out, "0044a320");
            printInstructions(out, "00493e30");
            printInstructions(out, "0044e400");
            printInstructions(out, "004b0630");
            printInstructions(out, "004b03a0");
            printRelevantStrings(out);
            printRawFamilyStrings(out);
        } finally {
            decompiler.dispose();
        }
    }
}
