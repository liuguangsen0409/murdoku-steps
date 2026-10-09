import type {CharacterId,CellId} from '../case/types';
export interface Reason {ruleId:string;clueRefs:string[];dependsOn:string[]}
export type Action={type:'blockCells';cells:CellId[];reason:Reason}|{type:'setCandidates';character:CharacterId;cells:CellId[]}|{type:'removeCandidate';character:CharacterId;cell:CellId;reason:Reason}|{type:'placeCharacter';character:CharacterId;cell:CellId;reason:Reason}|{type:'applyRowColumnConstraint';character:CharacterId;reason:Reason};
export interface Step {id:string;title:string;explanation:string;clueRefs:string[];focusCharacters:CharacterId[];candidateCharacters?:CharacterId[];highlightCells:CellId[];actions:Action[];rule?:string;details?:string[]}
export interface TutorialState {blockedCells?:CellId[];placements:Partial<Record<CharacterId,CellId>>;candidates:Record<CharacterId,CellId[]>;eliminations:{cell:CellId;character:CharacterId;reason:Reason}[]}
