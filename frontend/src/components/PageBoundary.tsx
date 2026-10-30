import {Component,type ReactNode} from 'react';
export default class PageBoundary extends Component<{children:ReactNode},{failed:boolean}>{
 state={failed:false};
 static getDerivedStateFromError(){return {failed:true}}
 render(){return this.state.failed?<section className="panel" role="alert"><h2>This page could not be displayed</h2><p>Your navigation is still available. Switch pages or retry this view.</p><button onClick={()=>this.setState({failed:false})}>Retry page</button></section>:this.props.children}
}
