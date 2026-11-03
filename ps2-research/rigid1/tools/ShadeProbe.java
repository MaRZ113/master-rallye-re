import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.*;
import ghidra.program.model.address.*;
import ghidra.program.model.listing.*;
import ghidra.program.model.symbol.*;
import java.nio.file.*;
import java.io.*;
import java.nio.charset.StandardCharsets;

// Read-only (COURSE-ALIVE4 shading/shadow probe). Arguments: out file, then items:
//   f:<hex>  decompile the function containing the address
//   x:<hex>  list every reference to the address with its containing function
public class ShadeProbe extends GhidraScript {
 public void run() throws Exception {
  String[] a=getScriptArgs();
  try(BufferedWriter w=Files.newBufferedWriter(Paths.get(a[0]),StandardCharsets.UTF_8)){
   w.write("LANGUAGE\t"+currentProgram.getLanguageID()+"\nSHA256\t"+currentProgram.getExecutableSHA256()+"\n");
   DecompInterface d=new DecompInterface(); d.openProgram(currentProgram);
   for(int k=1;k<a.length;k++){
    String kind=a[k].substring(0,1); Address at=toAddr(Long.parseLong(a[k].substring(2),16));
    if(kind.equals("x")){
     w.write("\n=== XREFS "+at+"\n");
     for(Reference r:getReferencesTo(at)){
      Function f=getFunctionContaining(r.getFromAddress());
      w.write(r.getFromAddress()+"\t"+r.getReferenceType()+"\t"+(f==null?"-":f.getEntryPoint().toString())+"\n");
     }
    } else {
     Function f=getFunctionContaining(at);
     if(f==null){w.write("\n=== NO FUNCTION "+at+"\n");continue;}
     w.write("\n=== FUNCTION "+f.getEntryPoint()+".."+f.getBody().getMaxAddress()+" (for "+at+")\n");
     DecompileResults r=d.decompileFunction(f,60,monitor);
     if(r.getDecompiledFunction()!=null)w.write(r.getDecompiledFunction().getC());
    }
   }
   d.dispose();
  }
 }
}
