// Export static string xrefs relevant to vehicle selection, race records,
// config brokers, wheels, and the vehicle physics subsystems.
// Arguments: <output-json>
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Data;
import ghidra.program.model.listing.DataIterator;
import ghidra.program.model.listing.Function;
import ghidra.program.model.symbol.Reference;
import ghidra.program.model.symbol.ReferenceIterator;
import java.io.BufferedWriter;
import java.io.FileOutputStream;
import java.io.OutputStreamWriter;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;

public class RPhys2VehicleStringXrefAudit extends GhidraScript {
    private String quote(String value) {
        StringBuilder out = new StringBuilder("\"");
        for (int i = 0; i < value.length(); i++) {
            char c = value.charAt(i);
            if (c == '\\' || c == '"') out.append('\\').append(c);
            else if (c == '\n') out.append("\\n");
            else if (c == '\r') out.append("\\r");
            else if (c == '\t') out.append("\\t");
            else if (c < 0x20) out.append(String.format("\\u%04x", (int)c));
            else out.append(c);
        }
        return out.append('"').toString();
    }

    private boolean isRelevant(String value) {
        String s = value.toLowerCase(Locale.ROOT);
        return s.contains("vehicles/") || s.contains("race/") ||
            s.contains("car%d") || s.contains("cartype") ||
            s.contains("carmodeldata") || s.contains("vehicleparam") ||
            s.contains("vehicleparams") || s.contains("vehicletype") ||
            s.contains("wheel") || s.contains("suspension") ||
            s.contains("chassis") || s.contains("engine") ||
            s.contains("damage");
    }

    private String functionName(Address address) {
        Function function = currentProgram.getFunctionManager().getFunctionContaining(address);
        return function == null ? "" : function.getName();
    }

    @Override
    public void run() throws Exception {
        if (getScriptArgs().length != 1) {
            printerr("Expected one argument: output JSON path");
            return;
        }
        String output = getScriptArgs()[0];
        List<Data> matches = new ArrayList<>();
        DataIterator iterator = currentProgram.getListing().getDefinedData(true);
        while (iterator.hasNext()) {
            monitor.checkCancelled();
            Data data = iterator.next();
            Object object = data.getValue();
            if (!(object instanceof String)) continue;
            String value = (String)object;
            if (isRelevant(value)) matches.add(data);
        }

        try (BufferedWriter out = new BufferedWriter(new OutputStreamWriter(
                new FileOutputStream(output), StandardCharsets.UTF_8))) {
            out.write("{\n  \"program\": " + quote(currentProgram.getName()) +
                ",\n  \"image_base\": " + quote(currentProgram.getImageBase().toString()) +
                ",\n  \"string_count\": " + matches.size() + ",\n  \"strings\": [\n");
            for (int i = 0; i < matches.size(); i++) {
                Data data = matches.get(i);
                Address address = data.getAddress();
                String value = (String)data.getValue();
                ReferenceIterator refs = currentProgram.getReferenceManager().getReferencesTo(address);
                List<String> xrefs = new ArrayList<>();
                while (refs.hasNext()) {
                    Reference reference = refs.next();
                    Address from = reference.getFromAddress();
                    xrefs.add("{\"from\": " + quote(from.toString()) +
                        ", \"type\": " + quote(reference.getReferenceType().toString()) +
                        ", \"read\": " + reference.getReferenceType().isRead() +
                        ", \"write\": " + reference.getReferenceType().isWrite() +
                        ", \"function\": " + quote(functionName(from)) + "}");
                }
                out.write("    {\"address\": " + quote(address.toString()) +
                    ", \"data_type\": " + quote(data.getDataType().getName()) +
                    ", \"value\": " + quote(value) +
                    ", \"xref_count\": " + xrefs.size() +
                    ", \"xrefs\": [" + String.join(", ", xrefs) + "]}");
                out.write(i + 1 == matches.size() ? "\n" : ",\n");
            }
            out.write("  ]\n}\n");
        }
        println("Wrote " + matches.size() + " relevant string records to " + output);
    }
}
