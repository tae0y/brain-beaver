import loremIpsumKR from "lorem-ipsum-kr";
import axios from 'axios';

interface Node {
  id: string;
  label: string;
  text: string;
  value: number;
  category: string;
}

interface Link {
  source: number;
  target: number;
}

const readyCallbacks: ((data: { pointPositions: Node[], links: number[] }) => void)[] = [];

function notifyReady() {
  readyCallbacks.forEach(callback => callback({ pointPositions, links }));
}

export function onDataReady(callback: (data: { pointPositions: Node[], links: number[] }) => void) {
  readyCallbacks.push(callback);
}

function getRandom(min: number, max: number): number {
  return Math.floor(Math.random() * (max - min) + min);
}

async function fetchConcepts() {
  try {
    //const response = await axios.get('http://bws_backend:8112/api/concepts');
    const concepts_response = await axios.get('http://localhost:8112/api/concepts');
    if (concepts_response.data.status === 'success') {
      const concepts = concepts_response.data.data;
      return concepts.map((concept: any) => ({
        id: concept.id,
        label: concept.keywords,
        text: concept.summary,
        value: concept.source_num + concept.target_num,
        category: concept.category
      }));
    } else {
      console.error('Failed to fetch concepts:', concepts_response.data.message);
      return [];
    }
  } catch (error) {
    console.error('Error fetching concepts:', error);
    return [];
  }
}

async function fetchNetworks(){
  try {
    //const response = await axios.get('http://bws_backend:8112/api/concepts');
    const networks_response = await axios.get('http://localhost:8112/api/networks');
    if (networks_response.data.status === 'success') {
      const networks = networks_response.data.data;
      const results = networks.map((network: any) => ({
        source: network.source_concept_id,
        target: network.target_concept_id
      }));
      return results
    } else {
      console.error('Failed to fetch concepts:', networks_response.data.message);
      return [];
    }
  } catch (error) {
    console.error('Error fetching concepts:', error);
    return [];
  }
}

let pointPositions: Node[] = [];
let links: Link[] = []; //source, target 순서로 flat하게

(async () => {
  pointPositions = await fetchConcepts();
  links = await fetchNetworks();
  if (pointPositions.length % 2 != 0) {
    pointPositions.push({
      id: -1,
      label: "dummy",
      text: "dummy",
      value: 0,
      category: "dummy"
    });
  }

  notifyReady();
})();

export { pointPositions, links };