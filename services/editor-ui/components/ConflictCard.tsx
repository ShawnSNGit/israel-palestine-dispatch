import React from 'react'

export default function ConflictCard({ item }: { item: any }){
  return (
    <div className="card">
      <div className="flex justify-between items-start">
        <div>
          <h4 className="font-semibold">Cluster (disagreement: {item.disagreement_score})</h4>
          <div className="text-sm text-slate-600">Rigor: {item.rigor_score ?? 'n/a'}</div>
        </div>
      </div>
      <div className="mt-3 space-y-2">
        {item.items?.map((it: any, idx: number)=> (
          <div key={idx} className="p-2 border rounded">
            <a className="font-medium text-indigo-700" href={it.url} target="_blank" rel="noreferrer">{it.title}</a>
            <div className="text-sm text-slate-600">Trust: {it.trust}</div>
            <blockquote className="text-sm mt-2">{it.excerpt}</blockquote>
          </div>
        ))}
      </div>
      <div className="mt-3">
        <details className="text-sm">
          <summary className="cursor-pointer text-slate-700">Suggested hedging & guidance</summary>
          <div className="mt-2 text-sm text-slate-600">Use the STEMpathize templates to attribute differences, prioritize human impact sensitivity, and route legal questions to the review queue.</div>
        </details>
      </div>
    </div>
  )
}
