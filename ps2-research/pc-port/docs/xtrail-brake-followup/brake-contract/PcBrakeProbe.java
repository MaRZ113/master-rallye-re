import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.*;
import ghidra.program.model.listing.*;
import java.nio.file.*;
import java.io.*;
public class PcBrakeProbe extends GhidraScript {public void run()throws Exception{
 if(!currentProgram.getExecutableSHA256().equalsIgnoreCase("bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4"))throw new Exception("Hash mismatch");
 try(BufferedWriter w=Files.newBufferedWriter(Paths.get(getScriptArgs()[0]))){DecompInterface d=new DecompInterface();d.openProgram(currentProgram);
 for(long va:new long[]{0x4ca1d0L}){disassemble(toAddr(va));Function f=createFunction(toAddr(va),null);if(f==null)f=getFunctionAt(toAddr(va));w.write("FUNCTION "+f.getEntryPoint()+".."+f.getBody().getMaxAddress()+"\n");for(Instruction i:currentProgram.getListing().getInstructions(f.getBody(),true)){StringBuilder b=new StringBuilder();for(byte x:i.getBytes())b.append(String.format("%02x",x&255));w.write("INS\t"+i.getAddress()+"\t"+b+"\t"+i+"\n");}DecompileResults r=d.decompileFunction(f,30,monitor);if(r.getDecompiledFunction()!=null)w.write(r.getDecompiledFunction().getC());}d.dispose();}}
}
