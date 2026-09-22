import React from 'react'

type Props = {
  date: string
  summary?: string
}

export default function DigestCard({ date, summary }: Props) {
  return (
    <article className="card">
      <h3 className="text-lg font-semibold">{date}</h3>
      <p className="text-slate-600 mt-2">{summary ?? 'STEMpathize daily synthesis'}</p>
      <div className="mt-3">
        <a className="text-indigo-600 hover:underline" href={`/digest/${date}`}>View digest</a>
      </div>
    </article>
  )
}
