export const ids = ['A','B','C','D','E','V'] as const;
export type CharacterId = typeof ids[number] | 'F' | 'G' | 'H' | 'I' | 'J' | 'K' | 'L' | 'M' | 'N' | 'O';
export type CellId = `R${number}C${number}`;
export interface Cell {id:CellId;row:number;col:number;roomId:number;occupiable:boolean;carpet:boolean;objectIds:number[];fill?:string;texture?:string;textureAsset?:string|null;water?:boolean}
export interface PlacedObject {id:string;kind:string;cells:CellId[];asset:string;x:number;y:number;width:number;height:number;carpet?:boolean}
export interface Character {id:CharacterId;name:string;portrait:string;clueId:string;clueZh:string;clueEn:string;role?:string}
export interface Room {id:number;label:string;cells:CellId[];fill:string}
export interface Puzzle {id:string;width:number;height:number;cells:Cell[];objects:PlacedObject[];rooms:Room[];characters:Character[];roomLabels?:{label:string;x:number;y:number}[];objectNames?:Record<number,string>;generalClues?:{id:string;text:string}[]}
