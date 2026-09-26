// Decompile focused retail runtime functions selected from string/xref review.
// Arguments: <output-text>
import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Function;
import ghidra.program.model.symbol.Reference;
import ghidra.program.model.symbol.ReferenceIterator;
import java.io.FileWriter;
import java.io.PrintWriter;

public class RPhys2FocusedFunctionAudit extends GhidraScript {
    private String[] targets = {
        "0042d0d0", "0043a800", "0043bb70", "0043e4c0",
        "0043eff0", "0043f020", "0043f0e0", "0043ed00", "00444060",
        "00442d40", "00444f90", "00444fa0",
        "00444fb0", "0044a320", "0044a8e0", "0044c780", "0044cf70",
        "0044d720", "0044de80", "0044e400", "0044ed50", "0048e2d0",
        "0048e820", "0048e9c0", "0048eb40",
        "0048fad0", "0048fb90", "004938c0", "004939b0", "00493a40",
        "00493be0", "00493e30", "00493fd0", "00493cb0", "00494730",
        "00495460", "004958e0", "0049b940", "0049c950", "0049cef0",
        "00493600", "004940a0", "00496d20", "00498090", "00499400",
        "0049a800", "0049b0c0", "0049e970", "004a01d0", "004a1a30",
        "004a32f0", "004abbd0", "004abce0", "004adf50", "004adfb0",
        "004b6a00", "004c0b20", "004f5eb0", "004f6310", "005c41ad",
        "004bc590"
    };

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
            for (String text : targets) {
                monitor.checkCancelled();
                Address address = toAddr(Long.parseLong(text, 16));
                Function function = currentProgram.getFunctionManager().getFunctionAt(address);
                if (function == null) function = currentProgram.getFunctionManager().getFunctionContaining(address);
                out.println("\n===== TARGET 0x" + text + " =====");
                if (function == null) {
                    out.println("NO_FUNCTION");
                    continue;
                }
                out.println("FUNCTION " + function.getName() + " ENTRY " + function.getEntryPoint());
                DecompileResults result = decompiler.decompileFunction(function, 120, monitor);
                if (result != null && result.decompileCompleted() && result.getDecompiledFunction() != null)
                    out.println(result.getDecompiledFunction().getC());
                else out.println("DECOMPILE_FAILED " + (result == null ? "null" : result.getErrorMessage()));
                out.println("CALLERS:");
                ReferenceIterator refs = currentProgram.getReferenceManager().getReferencesTo(function.getEntryPoint());
                while (refs.hasNext()) {
                    Reference reference = refs.next();
                    Function caller = currentProgram.getFunctionManager().getFunctionContaining(reference.getFromAddress());
                    out.println("  " + reference.getFromAddress() + " " + reference.getReferenceType() +
                        " caller=" + (caller == null ? "UNKNOWN" : caller.getName() + "@" + caller.getEntryPoint()));
                }
            }
        } finally {
            decompiler.dispose();
        }
    }
}
