import {useState} from 'react';
import CivilianProfile from '../pages/CivilianProfile';
import type {CivilianUser} from './CivilianSession';
import type {City} from '../types/api';
import {loadGuestState} from './guestStorage';
function loadUser():CivilianUser{const p=loadGuestState().profile??{};return {id:'guest',phone:'',name:typeof p.name==='string'?p.name:'Guest',email:typeof p.email==='string'?p.email:'',address:typeof p.address==='string'?p.address:''}}
export default function GuestProfile({city,revision}:{city:City|undefined;revision:number}){const [user,setUser]=useState(loadUser);return <CivilianProfile guest user={user} onUser={setUser} onLogout={async()=>{}} city={city} revision={revision}/>}
