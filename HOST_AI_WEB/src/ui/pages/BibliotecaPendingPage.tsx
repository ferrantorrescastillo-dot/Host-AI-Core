import { BibliotecaNav } from "../components/BibliotecaNav";

export function BibliotecaPendingPage({ title, detail }: { title: string; detail: string }) {
  return <section className="panel"><p className="eyebrow">Biblioteca Culinaria</p><h2>{title}</h2><BibliotecaNav /><div className="panel-state"><p>{detail}</p></div></section>;
}
