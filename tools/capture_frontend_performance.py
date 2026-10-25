"""Simple manual cold/warm/re-entry capture with automatic exact-one MR PID."""
import argparse,datetime,hashlib,json,re,subprocess,sys
from pathlib import Path
from vehicle_frontend_perf_capture import capture,find_binding
ROOT=Path(__file__).resolve().parents[1]


def running_game_pid():
    result=subprocess.run(['powershell.exe','-NoLogo','-NoProfile','-NonInteractive','-Command','Get-Process -Name MRallye -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Id'],capture_output=True,text=True)
    pids=[int(line.strip()) for line in result.stdout.splitlines() if line.strip().isdigit()]
    if len(pids)!=1:raise ValueError('Expected exactly one running MRallye process. Start the profiler candidate and close other game instances.')
    return pids[0]


def output_name(car,phase):
    if not re.fullmatch(r'[A-Za-z0-9_-]{1,48}',car) or phase not in ('cold','warm','reentry'):raise ValueError('Use a short car name and cold/warm/reentry phase')
    stamp=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=10))).strftime('%Y%m%d-%H%M%S-%f')
    return f'{stamp}-{car.lower()}-{phase}.json'


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--candidate',type=Path,required=True);p.add_argument('--car',help='Short user-selected vehicle label');p.add_argument('--phase',choices=['cold','warm','reentry']);p.add_argument('--seconds',type=int,choices=[20,30],default=30);p.add_argument('--output-dir',type=Path);a=p.parse_args(argv)
    if a.output_dir is None:a.output_dir=a.candidate/'captures'
    car=a.car or input('Vehicle name [Lancer / Subaru / Pajero / stockNavara]: ').strip()
    phase=a.phase or input('Test phase [cold / warm / reentry]: ').strip().lower()
    filename=output_name(car,phase);binding_file=a.candidate/'runtime/native-patch-manifest.json'
    if not binding_file.is_file():raise ValueError('Profiler candidate manifest not found: '+str(binding_file))
    binding=find_binding(json.loads(binding_file.read_text()));pid=running_game_pid()
    print(f'Found MRallye PID {pid}. Capture: {car}, {phase}, {a.seconds} seconds.')
    print('Keep the game open. After capture starts, perform exactly one selection or menu re-entry.')
    input('Press Enter to START recording, then switch to the game and perform the action: ')
    print('RECORDING. Perform the action now.',flush=True)
    report=capture(pid,binding,a.seconds,.1);report.update(label=car+'-'+phase,car=car,phase=phase,binding_file=str(binding_file),binding_sha256=hashlib.sha256(binding_file.read_bytes()).hexdigest())
    a.output_dir.mkdir(parents=True,exist_ok=True);output=a.output_dir/filename;output.write_text(json.dumps(report,indent=2)+'\n')
    print('Saved: '+str(output))
    for row in report['interval_summary']:print(f"{row['stage']}: {row['calls']} calls, {row['total_ms']:.3f} ms inclusive")
    return output


if __name__=='__main__':
    try:main()
    except (ValueError,OSError) as error:print('Capture failed: '+str(error),file=sys.stderr);sys.exit(1)
