// Adds conservative R-EXE1 types to the isolated retail Ghidra project.
// Run as a post-script on the existing retail project. No executable bytes change.
import ghidra.app.script.GhidraScript;
import ghidra.program.model.data.CategoryPath;
import ghidra.program.model.data.DataTypeConflictHandler;
import ghidra.program.model.data.DWordDataType;
import ghidra.program.model.data.StructureDataType;

public class AddRExe1RetailTypes extends GhidraScript {
    @Override
    protected void run() throws Exception {
        StructureDataType broker = new StructureDataType(
            new CategoryPath("/R-EXE1"), "BrokerEntry_Partial_0x1C", 0,
            currentProgram.getDataTypeManager());
        broker.add(DWordDataType.dataType, 4, "key_index_candidate",
            "Requested broker key/index; string interning relation not verified.");
        broker.add(DWordDataType.dataType, 4, "value_storage_pointer_candidate",
            "Pointer-like storage word; scalar diagnostics dereference it.");
        broker.add(DWordDataType.dataType, 4, "type_tag",
            "Observed Bool=0, Float=1, Int=2, Matrix=3, String=4; other tags partial.");
        broker.add(DWordDataType.dataType, 4, "save_flags",
            "Flag masks observed; exact SaveOptions/SavePlayerState bit mapping unverified.");
        broker.add(DWordDataType.dataType, 4, "revision",
            "Printed as Rev %d by broker diagnostic.");
        broker.add(DWordDataType.dataType, 4, "scope_tag",
            "Observed 0=GLOBAL, 1=SCENE; remaining categories unresolved.");
        broker.add(DWordDataType.dataType, 4, "unknown_18",
            "No stable interpretation assigned.");
        currentProgram.getDataTypeManager().addDataType(
            broker, DataTypeConflictHandler.REPLACE_HANDLER);
        println("Added /R-EXE1/BrokerEntry_Partial_0x1C to isolated retail project.");
    }
}
