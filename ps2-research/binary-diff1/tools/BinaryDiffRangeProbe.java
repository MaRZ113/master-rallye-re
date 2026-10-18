import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.*;
import ghidra.program.model.address.*;
import ghidra.program.model.listing.*;
import java.nio.file.*;
import java.io.*;
import java.nio.charset.StandardCharsets;

// Read-only: decompile every function whose entry lies in [lo,hi) for each "lo-hi" range argument.
public class BinaryDiffRangeProbe extends GhidraScript {
 public void run() throws Exception {
  String[] a=getScriptArgs();
  try(BufferedWriter w=Files.newBufferedWriter(Paths.get(a[0]),StandardCharsets.UTF_8)){
   w.write("LANGUAGE\t"+currentProgram.getLanguageID()+"\nSHA256\t"+currentProgram.getExecutableSHA256()+"\n");
   DecompInterface d=new DecompInterface(); d.openProgram(currentProgram);
   for(int k=1;k<a.length;k++){
    String[] p=a[k].split("-");
    Address lo=toAddr(Long.parseLong(p[0],16)), hi=toAddr(Long.parseLong(p[1],16));
    FunctionIterator it=currentProgram.getFunctionManager().getFunctions(lo,true);
    while(it.hasNext()){
     Function f=it.next(); if(f.getEntryPoint().compareTo(hi)>=0)break;
     w.write("\n=== FUNCTION "+f.getEntryPoint()+".."+f.getBody().getMaxAddress()+"\n");
     DecompileResults r=d.decompileFunction(f,30,monitor);
     if(r.getDecompiledFunction()!=null)w.write(r.getDecompiledFunction().getC());
    }
   }
   d.dispose();
  }
 }
}
