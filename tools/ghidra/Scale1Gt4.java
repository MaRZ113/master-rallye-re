// Private source-artifact evidence. Ghidra output is not original source.
// @category MasterRallye
import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.*;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.*;
import java.io.*;

public class Scale1Gt4 extends GhidraScript {
    public void run() throws Exception {
        String[] args=getScriptArgs();
        DecompInterface d=new DecompInterface();d.openProgram(currentProgram);
        try(PrintWriter out=new PrintWriter(args[0],"UTF-8")) {
            out.println("LANGUAGE="+currentProgram.getLanguageID());
            for(int i=1;i<args.length;i++) {
                Address a=toAddr(args[i]);Function f=getFunctionAt(a);
                if(f==null)f=getFunctionContaining(a);
                if(f==null){disassemble(a);createFunction(a,null);f=getFunctionAt(a);}
                out.println("\nADDRESS="+a+" FUNCTION="+f);
                if(f==null)continue;
                for(ghidra.program.model.symbol.Reference ref:getReferencesTo(f.getEntryPoint()))
                    out.println("INCOMING="+ref.getFromAddress()+" "+ref.getReferenceType());
                DecompileResults r=d.decompileFunction(f,60,monitor);
                out.println(r.decompileCompleted()?r.getDecompiledFunction().getC():r.getErrorMessage());
                InstructionIterator it=currentProgram.getListing().getInstructions(f.getBody(),true);
                while(it.hasNext()) {
                    Instruction ins=it.next();byte[] b=ins.getBytes();StringBuilder hex=new StringBuilder();
                    for(byte v:b)hex.append(String.format("%02x",v&255));
                    out.println(ins.getAddress()+" "+hex+" "+ins);
                }
            }
        }finally{d.dispose();}
    }
}
