import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.address.AddressSetView;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.Instruction;
import ghidra.program.model.listing.InstructionIterator;
import ghidra.program.model.listing.Listing;
import ghidra.program.model.symbol.Reference;
import ghidra.program.model.symbol.ReferenceIterator;
import java.io.BufferedWriter;
import java.io.FileWriter;
import java.io.PrintWriter;

public class DumpR5VHStackEvidence extends GhidraScript {
    @Override
    protected void run() throws Exception {
        String[] args = getScriptArgs();
        if (args.length != 1) {
            throw new IllegalArgumentException("usage: DumpR5VHStackEvidence.java <output.txt>");
        }
        try (PrintWriter out = new PrintWriter(new BufferedWriter(new FileWriter(args[0])))) {
            out.println("PROGRAM=" + currentProgram.getName());
            dumpReferences(out, "00458090");
            dumpInstructions(out, "0047B780", "0047B980");
            dumpInstructions(out, "00458090", "00458140");
            dumpInstructions(out, "00458320", "00458440");
            dumpInstructions(out, "00458980", "004589B0");
            dumpFunctionInstructions(out, "00458090");
            dumpFunctionInstructions(out, "00458980");
            dumpDecompilation(out, "0047B780");
            dumpDecompilation(out, "00458090");
            dumpDecompilation(out, "00458980");
        }
    }

    private void dumpReferences(PrintWriter out, String targetText) {
        Address target = toAddr(targetText);
        out.println("\nREFERENCES_TO=" + target);
        ReferenceIterator references = currentProgram.getReferenceManager().getReferencesTo(target);
        while (references.hasNext()) {
            Reference reference = references.next();
            Instruction instruction = currentProgram.getListing().getInstructionAt(reference.getFromAddress());
            out.println(reference.getFromAddress() + " type=" + reference.getReferenceType()
                + " instruction=" + (instruction == null ? "<none>" : instruction.toString()));
        }
    }

    private void dumpInstructions(PrintWriter out, String startText, String endText) throws Exception {
        Address start = toAddr(startText);
        Address end = toAddr(endText);
        Listing listing = currentProgram.getListing();
        out.println("\nDISASSEMBLY=" + start + ".." + end);
        InstructionIterator iterator = listing.getInstructions(start, true);
        while (iterator.hasNext()) {
            Instruction instruction = iterator.next();
            if (instruction.getAddress().compareTo(end) > 0) {
                break;
            }
            StringBuilder bytes = new StringBuilder();
            for (byte value : instruction.getBytes()) {
                bytes.append(String.format("%02X", value & 0xff));
            }
            out.println(instruction.getAddress() + "  " + instruction + "  bytes=" + bytes);
        }
    }

    private void dumpDecompilation(PrintWriter out, String entryText) {
        Address entry = toAddr(entryText);
        Function function = currentProgram.getFunctionManager().getFunctionAt(entry);
        out.println("\nDECOMPILATION=" + entry + " function=" + function);
        if (function == null) {
            out.println("<function not found>");
            return;
        }
        DecompInterface decompiler = new DecompInterface();
        try {
            decompiler.openProgram(currentProgram);
            DecompileResults result = decompiler.decompileFunction(function, 60, monitor);
            out.println(result.getDecompiledFunction() == null
                ? "<decompilation unavailable>"
                : result.getDecompiledFunction().getC());
        } finally {
            decompiler.dispose();
        }
    }

    private void dumpFunctionInstructions(PrintWriter out, String entryText) throws Exception {
        Address entry = toAddr(entryText);
        Function function = currentProgram.getFunctionManager().getFunctionAt(entry);
        out.println("\nFULL_FUNCTION_DISASSEMBLY=" + function);
        if (function == null) {
            out.println("<function not found>");
            return;
        }
        AddressSetView body = function.getBody();
        InstructionIterator iterator = currentProgram.getListing().getInstructions(body, true);
        while (iterator.hasNext()) {
            Instruction instruction = iterator.next();
            StringBuilder bytes = new StringBuilder();
            for (byte value : instruction.getBytes()) {
                bytes.append(String.format("%02X", value & 0xff));
            }
            out.println(instruction.getAddress() + "  " + instruction + "  bytes=" + bytes);
        }
    }
}
