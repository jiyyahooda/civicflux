import type {ComponentPropsWithoutRef,ReactNode} from 'react';
type Props=ComponentPropsWithoutRef<'section'>&{title:string;description?:string;children:ReactNode};
export default function OperationalPanel({title,description,children,className='',...props}:Props){return <section {...props} className={'panel operational-panel '+className}><header className="operational-heading"><h2>{title}</h2>{description&&<p>{description}</p>}</header><div className="operational-content">{children}</div></section>}
