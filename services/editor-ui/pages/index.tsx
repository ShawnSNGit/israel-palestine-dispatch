import fs from 'fs'
import path from 'path'
import Link from 'next/link'
import Header from '../components/Header'
import DigestCard from '../components/DigestCard'

export default function Home({ digests }: { digests: string[] }){
  return (
    <div>
      <Header />
      <main className="container mt-8">
        <h1 className="text-3xl font-bold mb-2">STEMpathize Dashboard</h1>
        <p className="text-slate-600 mb-6">A living, empathy-aware synthesis of sources. Click a digest to explore conflicts, evidence, and suggested hedging language.</p>

        <section>
          <h2 className="text-xl font-semibold mb-3">Recent Digests</h2>
          {digests.length === 0 && <p>No digests found</p>}
          {digests.map((d)=> (
            <DigestCard key={d} date={d} />
          ))}
        </section>

      </main>
    </div>
  )
}

export async function getStaticProps(){
  try{
    const idxPath = path.resolve(process.cwd(), '../../data/digests_index.json')
    const raw = fs.readFileSync(idxPath, 'utf-8')
    const idx = JSON.parse(raw)
    const dates = idx.map((i: any) => i.date).reverse()
    return { props: { digests: dates }, revalidate: 60 }
  }catch(e){
    return { props: { digests: [] } }
  }
}
