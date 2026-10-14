import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.*;
import ghidra.program.model.listing.*;
import ghidra.program.model.symbol.*;
import java.nio.file.*;
import java.io.*;
import java.nio.charset.StandardCharsets;

/** Read-only bounded EER probe; raw output remains ignored. */
public class BrakeModeProbe extends GhidraScript {
 public void run() throws Exception {
  if (!"r5900:LE:32:default".equals(currentProgram.getLanguageID().toString())) throw new Exception("Wrong R5900 language");
  if (!"b15a80c516986bfd7f9fcfcfa2ec5fbf37643778c6363dde460006d7001a78f2".equals(currentProgram.getExecutableSHA256().toLowerCase())) throw new Exception("Wrong ELF");
  try (BufferedWriter w=Files.newBufferedWriter(Paths.get(getScriptArgs()[0]),StandardCharsets.UTF_8)) {
   w.write("LANGUAGE\t"+currentProgram.getLanguageID()+"\nSHA256\t"+currentProgram.getExecutableSHA256()+"\n");
   DecompInterface d=new DecompInterface(); d.openProgram(currentProgram);
   FunctionIterator neighbors=currentProgram.getFunctionManager().getFunctions(toAddr(0x1a07e0L),true);
   for(int n=0;neighbors.hasNext()&&n<10;n++) {
    Function neighbor=neighbors.next();
    w.write("NEIGHBOR\t"+neighbor.getEntryPoint()+"\t"+neighbor.getBody().getMaxAddress()+"\n");
   }
   for(long va:new long[]{0x472498L,0x4724b0L,0x479ff8L,0x472300L}) {
    for(Reference ref:currentProgram.getReferenceManager().getReferencesTo(toAddr(va))) {
     Function owner=currentProgram.getFunctionManager().getFunctionContaining(ref.getFromAddress());
     w.write("STRINGREF\t"+Long.toHexString(va)+"\t"+ref.getFromAddress()+"\t"+(owner==null?"UNKNOWN":owner.getEntryPoint())+"\n");
    }
   }
   for (long va:new long[]{0x312610L,0x31cd98L,0x31e478L}) {
    Function f=currentProgram.getFunctionManager().getFunctionAt(toAddr(va));
    if (f==null) { w.write("UNKNOWN FUNCTION "+Long.toHexString(va)+"\n"); continue; }
    w.write("FUNCTION "+f.getEntryPoint()+".."+f.getBody().getMaxAddress()+"\n");
    for (Reference r:currentProgram.getReferenceManager().getReferencesTo(f.getEntryPoint())) w.write("CALLER\t"+r.getFromAddress()+"\t"+r.getReferenceType()+"\n");
    for (Instruction i:currentProgram.getListing().getInstructions(f.getBody(),true)) {
     StringBuilder b=new StringBuilder();for(byte x:i.getBytes())b.append(String.format("%02x",x&255));
     w.write("INS\t"+i.getAddress()+"\t"+b+"\t"+i+"\n");
    }
    DecompileResults out=d.decompileFunction(f,30,monitor);
    if(out.getDecompiledFunction()!=null)w.write(out.getDecompiledFunction().getC()+"\n");
   }
   d.dispose();
  }
 }
}
