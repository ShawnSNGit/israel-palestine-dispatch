import fs from 'fs'
import path from 'path'
import Header from '../../components/Header'
import ConflictCard from '../../components/ConflictCard'

export default function DigestPage({ machine }: { machine: any }){
  return (
    <div>
      <Header />
      <main className="container mt-8">
        <h1 className="text-2xl font-bold mb-2">STEMpathize Digest — {machine.generated_at}</h1>
        <p className="text-slate-600 mb-6">Total sources: {machine.total_sources}</p>

        <section>
          <h2 className="text-xl font-semibold mb-3">Conflicts</h2>
          {machine.conflicts.length === 0 && <p>No conflicts detected in this digest.</p>}
          {machine.conflicts.map((c: any, idx: number)=> (
            <ConflictCard key={idx} item={{...c, rigor_score: c.rigor_score}} />
          ))}
        </section>

      </main>
    </div>
  )
}

export async function getStaticPaths(){
  try{
    const idxPath = path.resolve(process.cwd(), '../../data/digests_index.json')
    const raw = fs.readFileSync(idxPath, 'utf-8')
    const idx = JSON.parse(raw)
    const paths = idx.map((i: any) => ({ params: { date: i.date } }))
    return { paths, fallback: 'blocking' }
  }catch(e){
    return { paths: [], fallback: 'blocking' }
  }
}

export async function getStaticProps({ params }: any){
  const date = params.date
  try{
    const machinePath = path.resolve(process.cwd(), `../../data/digest-STEMpathize-${date}.json`)
    const raw = fs.readFileSync(machinePath, 'utf-8')
    const machine = JSON.parse(raw)
    // compute simple rigor score per conflict
    for(const c of machine.conflicts){
      c.rigor_score = (c.rigor_score ?? 0) || (c.items ? Math.round((c.items.reduce((s: any, it: any)=> s + (it.trust||0), 0)/ (c.items.length||1)) * 1000)/1000 : 0)
    }
    return { props: { machine }, revalidate: 60 }
  }catch(e){
    return { notFound: true }
  }
}
