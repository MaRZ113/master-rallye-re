// Reconstructed original GT3 CORE static evidence; output remains private and ignored.
// @category MasterRallye
import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.*;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.*;
import ghidra.program.model.symbol.Reference;
import java.io.*;
import java.util.*;
import java.math.BigInteger;

public class Gt3SoundLab extends GhidraScript {
    private PrintWriter out;
    private DecompInterface decompiler;
    private Set<Address> done = new HashSet<>();
    private void dump(Address address) throws Exception {
        Function f=getFunctionAt(address);
        if(f==null)f=getFunctionContaining(address);
        if(f==null){disassemble(address); createFunction(address,null); f=getFunctionAt(address);}
        out.println("REQUEST="+address+" FUNCTION="+f);
        if(f==null || !done.add(f.getEntryPoint()))return;
        for(Reference ref:getReferencesTo(f.getEntryPoint()))
            out.println("INCOMING="+ref.getFromAddress()+" "+ref.getReferenceType());
        DecompileResults result=decompiler.decompileFunction(f,60,monitor);
        out.println(result.decompileCompleted()?result.getDecompiledFunction().getC():result.getErrorMessage());
        InstructionIterator it=currentProgram.getListing().getInstructions(f.getBody(),true);
        while(it.hasNext()){
            Instruction ins=it.next(); StringBuilder hex=new StringBuilder();
            for(byte b:ins.getBytes())hex.append(String.format("%02x",b&255));
            out.println(ins.getAddress()+" "+hex+" "+ins);
        }
    }
    public void run() throws Exception {
        String[] args=getScriptArgs();
        if(!"0ec332928ab4ff1ea48f9c36f57ca19019c1cfe4e3b3fbd3279176ee6cf110b9".equals(currentProgram.getExecutableSHA256()))
            throw new IllegalArgumentException("Unqualified reconstructed GT3 ELF SHA256");
        out=new PrintWriter(args[0],"UTF-8");
        // Exact GT3 entry bytes set GP=0x3579f0 and clear BSS from 0x353200.
        // This uninitialized block is an analysis aid, not extracted source data.
        if(currentProgram.getMemory().getBlock(toAddr("353200"))==null)
            currentProgram.getMemory().createUninitializedBlock("gt3_bss_inferred",toAddr("353200"),0x4b2c20-0x353200,false);
        currentProgram.getProgramContext().setValue(currentProgram.getRegister("gp"),toAddr("100000"),toAddr("4b2c1f"),new BigInteger("3579f0",16));
        decompiler=new DecompInterface();decompiler.openProgram(currentProgram);
        try{
            out.println("LANGUAGE="+currentProgram.getLanguageID());
            out.println("PROGRAM_SHA256="+currentProgram.getExecutableSHA256());
            for(int i=1;i<args.length;i++){
                if(args[i].startsWith("f:")){
                    String[] bounds=args[i].substring(2).split(":");
                    Address end=toAddr(bounds[1]);
                    FunctionIterator functions=currentProgram.getFunctionManager().getFunctions(toAddr(bounds[0]),true);
                    while(functions.hasNext()){
                        Function f=functions.next();
                        if(f.getEntryPoint().compareTo(end)>=0)break;
                        dump(f.getEntryPoint());
                    }
                }else if(args[i].startsWith("r:")){
                    Address addr=toAddr(args[i].substring(2));
                    out.println("DATA_REFS="+addr);
                    for(Reference ref:getReferencesTo(addr)){
                        out.println("DATA_REF="+ref);
                        Function f=getFunctionContaining(ref.getFromAddress());
                        if(f!=null)dump(f.getEntryPoint());
                    }
                }else if(args[i].startsWith("s:")){
                    String needle=args[i].substring(2);
                    DataIterator dataIt=currentProgram.getListing().getDefinedData(true);
                    while(dataIt.hasNext()){
                        Data data=dataIt.next();
                        Object value=data.getValue();
                        if(value instanceof String && value.toString().contains(needle)){
                            out.println("STRING="+data.getAddress()+" "+value);
                            for(Reference ref:getReferencesTo(data.getAddress())){
                                out.println("STRING_REF="+ref);
                                Function f=getFunctionContaining(ref.getFromAddress());
                                if(f!=null)dump(f.getEntryPoint());
                            }
                        }
                    }
                }else dump(toAddr(args[i]));
            }
        }finally{decompiler.dispose();out.close();}
    }
}
