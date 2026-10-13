#!/usr/bin/env python3
"""Read-only legacy build inventory. Never removes or relocates anything."""
import hashlib,json,os,subprocess,sys,zipfile
from pathlib import Path
PORT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def inventory():
    command=['powershell','-NoProfile','-Command',
        'Get-CimInstance Win32_Process | Select-Object Name,ProcessId,CommandLine | ConvertTo-Json -Compress']
    try:
        raw=subprocess.check_output(command,text=True,stderr=subprocess.STDOUT)
        processes=json.loads(raw) if raw.strip() else []
        if isinstance(processes,dict):processes=[processes]
        process_status='COMMAND_LINES_INSPECTED_NOT_OPEN_HANDLE_PROOF'
    except (OSError,ValueError,subprocess.CalledProcessError):
        processes=[];process_status='PROCESS_INSPECTION_UNAVAILABLE'
    archived=set()
    for archive in sorted((PORT/'dist').glob('*.zip')):
        with zipfile.ZipFile(archive) as z:
            # All small source members and DLLs; never proprietary/private assets.
            for member in z.infolist():
                if not member.is_dir():archived.add(hashlib.sha256(z.read(member)).hexdigest())
    current={sha(p) for folder in ('renderer','tests','docs') for p in (PORT/folder).rglob('*') if p.is_file()}
    rows=[]
    for folder in sorted(PORT.glob('.build-overlay*')):
        if not folder.is_dir():continue
        total=0;count=0;dlls=[];unique=[];reports=[];source_count=0
        for directory,_,files in os.walk(folder):
            for name in files:
                p=Path(directory)/name;total+=p.stat().st_size;count+=1
                relative=p.relative_to(folder).as_posix()
                # PDB/OBJ/intermediate DLLs are compiler output; inspect final DLLs,
                # saved reports and PS2 implementation snapshots for unique work.
                source='/ps2-research/pc-port/' in '/'+relative and p.suffix in ('.cpp','.hpp','.py')
                final=p.name=='d3d8.dll' and p.parent.name=='Release'
                report=p.name=='build-report.json'
                if source or final or report:
                    digest=sha(p);protected=digest in archived or digest in current
                    if source:source_count+=1
                    if final:dlls.append({'path':relative,'sha256':digest,'covered_by_handoff':digest in archived})
                    if report:reports.append(relative)
                    if not protected:unique.append({'path':relative,'sha256':digest,'kind':'SOURCE' if source else 'DLL' if final else 'REPORT'})
        matches=[{'name':p['Name'],'pid':p['ProcessId']} for p in processes if str(folder).lower() in (p.get('CommandLine') or '').lower()]
        status='PRESERVE_ACTIVE' if matches else 'PRESERVE_UNIQUE_OR_UNARCHIVED' if unique else 'CANDIDATE_AFTER_EXPLICIT_APPROVAL'
        rows.append({'directory':folder.name,'bytes':total,'mib':round(total/1048576,2),'files':count,
            'process_command_matches':matches,'process_status':process_status,'dlls':dlls,
            'ps2_source_files_inspected':source_count,'saved_reports':reports,'unique_or_unarchived':unique,
            'cleanup_status':status})
    return {'policy':'READ_ONLY_NO_DELETIONS','total_legacy_bytes':sum(r['bytes'] for r in rows),'directories':rows,
        'uniqueness_scope':'Compared final DLLs, PS2 source snapshots and reports to current sources and all existing handoff members; compiler/PDB/cache intermediates not preservation-oracle checked',
        'limitations':'No open-handle guarantee. Recheck activity and preserve unique evidence before any approved deletion.'}
if __name__=='__main__':
    result=inventory();destination=PORT/'docs/build-policy/legacy-inventory.json'
    destination.parent.mkdir(parents=True,exist_ok=True);destination.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'report':str(destination),'total_gib':round(result['total_legacy_bytes']/1073741824,2),
        'directories':[{k:r[k] for k in ('directory','mib','cleanup_status','process_command_matches')} for r in result['directories']]},indent=2))
