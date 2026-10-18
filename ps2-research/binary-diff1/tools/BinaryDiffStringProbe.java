import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.*;
import ghidra.program.model.listing.*;
import ghidra.program.model.mem.*;
import ghidra.program.model.symbol.*;
import java.nio.file.*;
import java.io.*;
import java.util.*;
import java.nio.charset.StandardCharsets;

// Read-only: finds ASCII needles, walks back to string start, lists references and containing functions.
public class BinaryDiffStringProbe extends GhidraScript {
 public void run() throws Exception {
  String[] a=getScriptArgs();
  List<String> needles=Files.readAllLines(Paths.get(a[1]),StandardCharsets.UTF_8);
  Memory mem=currentProgram.getMemory();
  ReferenceManager rm=currentProgram.getReferenceManager();
  FunctionManager fm=currentProgram.getFunctionManager();
  try(BufferedWriter w=Files.newBufferedWriter(Paths.get(a[0]),StandardCharsets.UTF_8)){
   w.write("LANGUAGE\t"+currentProgram.getLanguageID()+"\nSHA256\t"+currentProgram.getExecutableSHA256()+"\n");
   for(String n:needles){
    n=n.trim(); if(n.isEmpty())continue;
    byte[] nb=n.getBytes(StandardCharsets.US_ASCII);
    Address start=mem.getMinAddress(); int hits=0; Set<Address> seen=new HashSet<>();
    while(start!=null && hits<12){
     Address h=mem.findBytes(start,nb,null,true,monitor);
     if(h==null)break;
     start=h.add(1);
     // walk back to string start
     Address s=h; int back=0;
     while(back<96){ try{ byte b=mem.getByte(s.subtract(1)); if(b==0||b<0x20||b>0x7e)break; }catch(Exception e){break;} s=s.subtract(1); back++; }
     if(!seen.add(s))continue; hits++;
     StringBuilder t=new StringBuilder(); Address p=s;
     for(int i=0;i<80;i++){ byte b=mem.getByte(p); if(b==0)break; t.append((char)b); p=p.add(1);}
     w.write("NEEDLE\t"+n+"\tSTR\t"+s+"\t"+t+"\n");
     int r=0;
     for(Reference ref:rm.getReferencesTo(s)){
      if(r++>=10)break;
      Function f=fm.getFunctionContaining(ref.getFromAddress());
      w.write("  REF\t"+ref.getFromAddress()+"\t"+ref.getReferenceType()+"\tFUNC\t"+(f==null?"NONE":f.getEntryPoint()+" "+f.getName())+"\n");
     }
    }
   }
  }
 }
}
