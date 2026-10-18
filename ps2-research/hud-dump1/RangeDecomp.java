import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Function;
import java.nio.file.*;
import java.util.*;

/** Read-only: decompile every function overlapping [lo,hi) and write C to the output file. Args: lo hi out */
public class RangeDecomp extends ghidra.app.script.GhidraScript {
    @Override public void run() throws Exception {
        String[] a = getScriptArgs();
        long lo = Long.decode(a[0]), hi = Long.decode(a[1]);
        DecompInterface d = new DecompInterface(); d.openProgram(currentProgram);
        StringBuilder sb = new StringBuilder();
        Set<Address> seen = new LinkedHashSet<>();
        for (long va = lo; va < hi; va += 4) {
            Function f = getFunctionContaining(toAddr(va));
            if (f == null || !seen.add(f.getEntryPoint())) continue;
            DecompileResults r = d.decompileFunction(f, 90, monitor);
            sb.append("// ===== ").append(f.getEntryPoint()).append(' ').append(f.getName()).append(" size=").append(f.getBody().getNumAddresses()).append('\n');
            sb.append(r.decompileCompleted() ? r.getDecompiledFunction().getC() : "// FAILED " + r.getErrorMessage()).append('\n');
        }
        d.dispose();
        Files.write(Paths.get(a[2]), sb.toString().getBytes("UTF-8"));
        println("functions " + seen.size());
    }
}
