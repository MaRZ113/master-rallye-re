import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.*;
import ghidra.program.model.listing.*;
import ghidra.program.model.symbol.*;
import java.nio.file.*;import java.io.*;import java.nio.charset.StandardCharsets;
public class FrontendMaterialProbe extends GhidraScript {
 public void run() throws Exception {
  if(!"r5900:LE:32:default".equals(currentProgram.getLanguageID().toString()))throw new Exception("Wrong R5900 language");
  if(!"b15a80c516986bfd7f9fcfcfa2ec5fbf37643778c6363dde460006d7001a78f2".equals(currentProgram.getExecutableSHA256().toLowerCase()))throw new Exception("Wrong ELF");
  try(BufferedWriter w=Files.newBufferedWriter(Paths.get(getScriptArgs()[0]),StandardCharsets.UTF_8)) {
   w.write("LANGUAGE\t"+currentProgram.getLanguageID()+"\nSHA256\t"+currentProgram.getExecutableSHA256()+"\n");
   DecompInterface d=new DecompInterface();d.openProgram(currentProgram);
   for(long va:new long[]{0x3ae150L,0x3a6b70L,0x390f98L,0x3ada88L}) {
    Function f=currentProgram.getFunctionManager().getFunctionAt(toAddr(va));if(f==null){w.write("UNKNOWN "+Long.toHexString(va)+"\n");continue;}
    w.write("FUNCTION "+f.getEntryPoint()+".."+f.getBody().getMaxAddress()+"\n");
    for(Instruction i:currentProgram.getListing().getInstructions(f.getBody(),true)){StringBuilder b=new StringBuilder();for(byte x:i.getBytes())b.append(String.format("%02x",x&255));w.write("INS\t"+i.getAddress()+"\t"+b+"\t"+i+"\n");}
    DecompileResults r=d.decompileFunction(f,30,monitor);if(r.getDecompiledFunction()!=null)w.write(r.getDecompiledFunction().getC()+"\n");
   }
   for(long va:new long[]{0x3a6b70L,0x49b890L,0x3ada88L}){ReferenceIterator refs=currentProgram.getReferenceManager().getReferencesTo(toAddr(va));while(refs.hasNext()){Reference r=refs.next();w.write("REF\t"+Long.toHexString(va)+"\t"+r.getFromAddress()+"\t"+r.getReferenceType()+"\n");}}
   d.dispose();
  }
 }
}
