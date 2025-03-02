import axios from 'axios';

/*********************************************************************************************
 * 
 * basic
 * 
 * 
 *********************************************************************************************/
interface Node {
  id: string;
  label: string;
  text: string;
  value: number;
  category: string;
}

//['#88C6FF', '#FF99D2', '#2748A4'];
const colors = [
   [0.15294117647058825 , 0.2823529411764706 , 0.6431372549019608] //blue 2748A4
  ,[0.5333333333333333  , 0.7764705882352941 , 1] //skyblue 88C6FF
  ,[1                   , 0.6                , 0.8235294117647058]                 //palepink FF99D2
];

function getRandom(min: number, max: number): number {
  return Math.random() * (max - min) + min;
}


/*********************************************************************************************
 * 
 * fetch, gen data
 * 
 * 
 *********************************************************************************************/

async function fetchPointPositions() {
  try {
    //const response = await axios.get('http://bws_backend:8112/api/concepts');
    const concepts_response = await axios.get('http://localhost:8112/api/concepts');
    if (concepts_response.data.status === 'success') {
      const concepts = concepts_response.data.data;
      const results = new Float32Array(concepts.length * 2);
      for (let i = 0; i < concepts.length; i++) {
        const concept = concepts[i];
        results[concepts[i].id * 2]     = getRandom(1,concepts.length);
        results[concepts[i].id * 2 + 1] = getRandom(1,concepts.length);
      }
      pointPositions = results;
      pointColors = fetchPointColors();
      pointSizes  = fetchPointSizes(concepts_response.data.data);

    } else {
      console.error('Failed to fetch concepts:', concepts_response.data.message);
      return [];
    }
  } catch (error) {
    console.error('Error fetching concepts:', error);
    return [];
  }
}

async function fetchLinks(){
  try {
    //const response = await axios.get('http://bws_backend:8112/api/concepts');
    const networks_response = await axios.get('http://localhost:8112/api/networks');
    if (networks_response.data.status === 'success') {
      const networks = networks_response.data.data;
      const results = new Float32Array(networks.length * 2);
      for (let i = 0; i < networks.length; i++) {
        const network = networks[i];
        results[i * 2] = network.source_concept_id;
        results[i * 2 + 1] = network.target_concept_id;
      }
      links = results;
      linkColors = fetchLinkColors();
      linkWidths = fetchLinkWidths();
    } else {
      console.error('Failed to fetch concepts:', networks_response.data.message);
    }
  } catch (error) {
    console.error('Error fetching concepts:', error);
  }

}

function fetchPointColors(){
  const results = new Float32Array(pointPositions.length / 2 * 4);
  for (let i = 0; i < pointPositions.length/2; i++) {
    //const pointColor = getRgbaColor(pointColorScale(i % 1000))
    const pointColor   = colors[Math.floor(getRandom(0, colors.length))];
    results[i * 4]     = pointColor[0]
    results[i * 4 + 1] = pointColor[1]
    results[i * 4 + 2] = pointColor[2]
    results[i * 4 + 3] = 0.9
  }
  return results;
}

//todo : 백엔드와 프론트가 동일한 객체 정의를 공유할 수는 없을까?
function fetchPointSizes(concept_list: any[]){
  const results = new Float32Array(pointPositions.length / 2);
  for (let i = 0; i < pointPositions.length/2; i++) {
    const link_num = concept_list[i].source_num + concept_list[i].target_num
    results[i * 4]     = getRandom(link_num, link_num+1);
  }
  return results;
}

function fetchLinkColors(){
  const results = new Float32Array(links.length / 2 * 4);
  for (let i = 0; i < links.length/2; i++) {
    //const linkColor = getRgbaColor(linkColorScale(i % 1000))
    const linkColor   = colors[Math.floor(getRandom(0, colors.length))];
    results[i * 4]     = linkColor[0]
    results[i * 4 + 1] = linkColor[1]
    results[i * 4 + 2] = linkColor[2]
    results[i * 4 + 3] = 0.7
  }
  return results;
}

function fetchLinkWidths(){
  const results = new Float32Array(links.length / 2);
  for (let i = 0; i < links.length/2; i++) {
    results[i * 4]     = getRandom(0.1, 0.5);
  }
  return results;
}


/*********************************************************************************************
 * 
 * async callback
 * 
 * 
 *********************************************************************************************/

const readyCallbacks: ((data: { pointPositions: Float32Array, links: Float32Array }) => void)[] = [];

function notifyReady() {
  readyCallbacks.forEach(callback => callback({ pointPositions, links }));
}

export function onDataReady(callback: (data: { pointPositions: Float32Array, links: Float32Array }) => void) {
  readyCallbacks.push(callback);
}


/*********************************************************************************************
 * 
 * Export
 * 
 * 
 *********************************************************************************************/

let pointPositions: Float32Array;
let pointColors: Float32Array;
let pointSizes: Float32Array;
let links: Float32Array; //source, target 순서로 flat하게
let linkColors: Float32Array;
let linkWidths: Float32Array;

(async () => {
  await fetchPointPositions();
  await fetchLinks();
  notifyReady();
})();

export {
  pointPositions
  , pointColors
  , pointSizes
  , links
  , linkColors
  , linkWidths
};