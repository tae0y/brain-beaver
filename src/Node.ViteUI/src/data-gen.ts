import loremIpsumKR from "lorem-ipsum-kr";

interface Node {
  id: number;
  label: string;
  text: string;
  value: number;
  category: string;
}

function getRandom(min: number, max: number): number {
    return Math.random() * (max - min) + min;
  }

const numNodes = 20000;
const pointPositions: Node[] = Array.from({ length: numNodes }, (_, i) => ({
  id: i + 1,
  label: `노드 ${i + 1}`,
  text: loremIpsumKR(),
  value: Math.floor(Math.random() * 100) + 1,
  category: String.fromCharCode(65 + Math.floor(Math.random() * 26))
}));

const numLinks = Math.floor(numNodes * 2);
const links: number[] = [];
Array.from({ length: numLinks }, () => (
  links.push(Math.floor(Math.random() * numNodes) + 1),
  links.push(Math.floor(Math.random() * numNodes) + 1)
));

export { pointPositions, links };