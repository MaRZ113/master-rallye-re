"""Read user-supplied GT4 Beta handling rows without distributing game data.

Admits the 37/113/45/21-byte row layouts only. Metadata interpretation is
reported separately from recovered bytes; no automatic MR physics transplant.
"""
import argparse,json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from master_rallye.addon_sdk.gt4_spec import DatabaseTable,label_id

def inspect(folder,labels):
    sizes={'CHASSIS':37,'ENGINE':113,'GEAR':45,'DRIVETRAIN':21};raw={};evidence={}
    if set(labels)!=set(sizes):raise ValueError('explicit labels for four handling tables required')
    for table,label in labels.items():
        db=DatabaseTable((folder/(table+'.dbt')).read_bytes());i=label_id((folder/(table+'.idi')).read_bytes(),label);row=db.row(i)
        if len(row)!=sizes[table]:raise ValueError('unqualified GT4 handling row layout '+table)
        raw[table]=row;evidence[table]={**db.evidence(i),'label':label}
    s=lambda table,offset:struct.unpack_from('<h',raw[table],offset)[0]
    e=raw['ENGINE'];count=e[84]
    if not 2<=count<=24:raise ValueError('GT4 torque sample count outside layout')
    samples=[{'rpm_code':e[85+i],'torque_code':s('ENGINE',30+2*i)} for i in range(count)]
    if any(b['rpm_code']<=a['rpm_code'] for a,b in zip(samples,samples[1:])):raise ValueError('GT4 torque rpm codes not monotonic')
    return {'status':'RECOVERED_PRIVATE_SOURCE_ROWS_METADATA_INTERPRETATION', 'rows':evidence,
        'chassis':{'length_code':s('CHASSIS',0),'height_code':s('CHASSIS',2),'wheelbase_code':s('CHASSIS',4),'mass_code':s('CHASSIS',6)},
        'engine':{'display_ps_code':s('ENGINE',26),'display_torque_code':s('ENGINE',28),'shift_code':e[80],'revlimit_code':e[81],'samples':samples},
        'gear':{'forward_ratio_codes':[s('GEAR',i*2) for i in range(11)],'reverse_ratio_code':s('GEAR',22),'final_min_code':s('GEAR',24),'final_max_code':s('GEAR',26),'final_default_code':s('GEAR',28),'nshift_code':raw['GEAR'][36]},
        'drivetrain':{'drive_type_code':raw['DRIVETRAIN'][16],'type4wd_codes':list(raw['DRIVETRAIN'][17:21])},
        'interpretation_boundary':'Recovered bytes and schema offsets are reproducible. PDTools Beta metadata names are comparative evidence, not source ELF physics proof. mm, kg, rpm*100, kgf-m/100 and final-ratio/1000 interpretations are documented separately; MR coefficients are not copied blindly. Zero generated gear ratios are not usable explicit ratios.'}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--spec-folder',type=Path,required=True);p.add_argument('--labels',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    r=inspect(a.spec_folder,json.loads(a.labels.read_text()));a.output.write_text(json.dumps(r,indent=2)+'\n');print(r['status'])
