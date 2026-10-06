import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.address.AddressSet;
import ghidra.program.model.listing.Instruction;
import ghidra.program.model.listing.InstructionIterator;
import ghidra.program.model.listing.Listing;
import java.io.BufferedWriter;
import java.io.FileWriter;
import java.io.PrintWriter;

public class VerifyR5VH0Candidate extends GhidraScript {
    @Override
    protected void run() throws Exception {
        String[] args = getScriptArgs();
        if (args.length != 1) {
            throw new IllegalArgumentException("usage: VerifyR5VH0Candidate.java <output.txt>");
        }
        try (PrintWriter out = new PrintWriter(new BufferedWriter(new FileWriter(args[0])))) {
            out.println("PROGRAM=" + currentProgram.getName());
            dumpInstructions(out, "00458428", "0045842D");
            dumpInstructions(out, "0068E690", "0068E6C1");
        }
    }

    private void dumpInstructions(PrintWriter out, String startText, String endText) throws Exception {
        Address start = toAddr(startText);
        Address end = toAddr(endText);
        Listing listing = currentProgram.getListing();
        out.println("\nDISASSEMBLY=" + start + ".." + end);
        InstructionIterator instructions = listing.getInstructions(new AddressSet(start, end), true);
        while (instructions.hasNext()) {
            Instruction instruction = instructions.next();
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
}
