// Assemble an x86 code cave with Ghidra's assembler and print the bytes as hex.
// Usage (headless, -readOnly): AsmCave.java <out.txt> <hex base address> <source.asm>
// Source: one instruction per line, "label:" lines, ';' comments.
// Branch targets may name labels; they are resolved in fixed-point passes.
import ghidra.app.script.GhidraScript;
import ghidra.app.plugin.assembler.*;
import ghidra.app.plugin.assembler.sleigh.sem.*;
import ghidra.program.model.address.*;
import java.nio.file.*;
import java.util.*;

public class AsmCave extends GhidraScript {
  // Shortest fully-specified encoding without an operand-size prefix (0x66): in 32-bit code a
  // 66-prefixed CALL/JMP/Jcc takes a rel16 target and truncates EIP.
  byte[] pick(Assembler asm, Address at, String ins) throws Exception {
    AssemblyResolutionResults res = asm.resolveLine(at, ins);
    byte[] best = null;
    for (AssemblyResolution r : res) {
      if (!(r instanceof AssemblyResolvedPatterns)) continue;
      AssemblyPatternBlock blk = ((AssemblyResolvedPatterns) r).getInstruction();
      byte[] v = blk.getVals();
      boolean sizePrefix = false;
      for (byte x : v) {
        int p = x & 0xff;
        if (p == 0x66 || p == 0x67) { sizePrefix = true; break; }
        if (p != 0xf2 && p != 0xf3 && p != 0x2e && p != 0x3e && p != 0x26 && p != 0x36 && p != 0x64 && p != 0x65) break;
      }
      if (sizePrefix) continue;
      if (best == null || v.length < best.length) best = v;
    }
    if (best == null) throw new Exception("no non-66 encoding for: " + ins);
    return best;
  }

  public void run() throws Exception {
    String[] a = getScriptArgs();
    Path out = Paths.get(a[0]);
    long base = Long.parseLong(a[1], 16);
    List<String> src = new ArrayList<>();
    for (String l : Files.readAllLines(Paths.get(a[2]))) {
      int c = l.indexOf(';'); if (c >= 0) l = l.substring(0, c);
      l = l.trim(); if (!l.isEmpty()) src.add(l);
    }
    Assembler asm = Assemblers.getAssembler(currentProgram);
    Map<String, Long> labels = new HashMap<>();
    byte[][] code = null; long[] addr = null;
    for (int pass = 0; pass < 8; pass++) {
      List<byte[]> bytes = new ArrayList<>(); List<Long> where = new ArrayList<>();
      Map<String, Long> next = new HashMap<>();
      long pc = base;
      for (String l : src) {
        if (l.endsWith(":")) { next.put(l.substring(0, l.length() - 1), pc); continue; }
        String ins = l;
        for (Map.Entry<String, Long> e : labels.entrySet())
          ins = ins.replaceAll("\\b" + e.getKey() + "\\b", "0x" + Long.toHexString(e.getValue()));
        if (ins.matches(".*\\b[A-Za-z_][A-Za-z0-9_]*_lbl\\b.*"))
          ins = ins.replaceAll("\\b[A-Za-z_][A-Za-z0-9_]*_lbl\\b", "0x" + Long.toHexString(pc + 2));
        Address at = toAddr(pc);
        byte[] b = pick(asm, at, ins);
        bytes.add(b); where.add(pc); pc += b.length;
      }
      boolean stable = next.equals(labels);
      labels = next;
      code = bytes.toArray(new byte[0][]);
      addr = where.stream().mapToLong(Long::longValue).toArray();
      if (stable && pass > 0) break;
    }
    StringBuilder hex = new StringBuilder(); StringBuilder lst = new StringBuilder();
    int k = 0;
    for (String l : src) {
      if (l.endsWith(":")) { lst.append(l).append("\n"); continue; }
      StringBuilder h = new StringBuilder();
      for (byte x : code[k]) h.append(String.format("%02x", x & 0xff));
      lst.append(String.format("%08x  %-24s %s%n", addr[k], h, l));
      hex.append(h); k++;
    }
    Files.writeString(out, "HEX " + hex + "\n" + lst);
  }
}
