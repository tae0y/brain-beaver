import axios from 'axios';

/*********************************************************************************************
 * 
 * basic
 * 
 * 
 *********************************************************************************************/
interface Concept {
  id          :number,
  title       :string,
  keywords    :string,
  category    :string,
  summary     :string,
  status      :string,
  data_name   :string,
  source_num  :number,
  target_num  :number,
  create_time :string,
  update_time :string,
  embedding   :Array<number>,
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
      const concepts: Concept[] = concepts_response.data.data;
      const results = new Float32Array(concepts.length * 2);
      for (let i = 0; i < concepts.length; i++) {
        const concept = concepts[i];
        results[concept.id * 2]     = getRandom(1,concepts.length);
        results[concept.id * 2 + 1] = getRandom(1,concepts.length);
      }

      // point
      pointPositions = results;
      // color, list
      pointColors = fetchPointColors();
      pointSizes  = fetchPointSizes(concepts_response.data.data);
      // raw data
      conceptsRawDataList = concepts_response.data.data;

      // labels create
      pointLabelToIndex = new Map<string, number>();
      pointIndexToLabel = new Map<number, string>();
      for (let i = 0; i < concepts.length; i++) {
        const concept = concepts[i];
        //pointLabelToIndex.set(`${concept.id}: ${concept.title}` , concept.id);
        //pointIndexToLabel.set(concept.id, `${concept.id}: ${concept.title}`);
        pointLabelToIndex.set(`${concept.id}` , concept.id);
        pointIndexToLabel.set(concept.id, `${concept.id}`);
      }
      // labels display
      const concepts_sorted = concepts.sort( (a, b) => { if (a.source_num + a.target_num > b.source_num + b.target_num) { return -1; } else if (a.source_num + a.target_num < b.source_num + b.target_num) { return 1; } return 0; });
      for (let i = 0; i < concepts.length/10; i++) {
        pointsToShowLabelsFor.push(`${concepts_sorted[i].id}`);
      }

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

      // links
      links = results;

      // link color, width
      linkColors = fetchLinkColors();
      linkWidths = fetchLinkWidths();

      // fullyMappedNetwork
      for(let i=0; i<networks.length; i++){
        const source_key = `${networks[i].source_concept_id}`; //source->target
        const source_element = fullyMappedNetwork.get(source_key) ?? new Array<number>();
        source_element?.push(networks[i].target_concept_id);
        fullyMappedNetwork.set(source_key, source_element);

        const target_key = `${networks[i].target_concept_id}`; //target->source
        const target_element = fullyMappedNetwork.get(target_key) ?? new Array<number>();
        target_element?.push(networks[i].source_concept_id);
        fullyMappedNetwork.set(target_key, target_element);
      }

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
    results[i * 4 + 3] = 0.8
  }
  return results;
}

//todo : 백엔드와 프론트가 동일한 객체 정의를 공유할 수는 없을까?
function fetchPointSizes(concept_list: Concept[]){
  const results = new Float32Array(pointPositions.length / 2);
  for (let i = 0; i < pointPositions.length/2; i++) {
    const concept = concept_list[i]
    const link_num = concept.source_num + concept.target_num
    results[concept.id] = link_num * 1.2 + 2;
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
    results[i * 4 + 3] = 1;
  }
  return results;
}

function fetchLinkWidths(){
  const results = new Float32Array(links.length / 2);
  for (let i = 0; i < links.length/2; i++) {
    results[i * 4]     = getRandom(0.1, 0.2);
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
let conceptsRawDataList: any[];
let pointPositions     : Float32Array;
let pointColors        : Float32Array;
let pointSizes         : Float32Array;
let links              : Float32Array; //source, target 순서로 flat하게
let linkColors         : Float32Array;
let linkWidths         : Float32Array;
let pointLabelToIndex  : Map<string, number>;
let pointIndexToLabel  : Map<number, string>;
let pointsToShowLabelsFor: string[] = [];
let fullyMappedNetwork : Map<string, Array<number>> = new Map<string, Array<number>>();

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
  , pointIndexToLabel
  , pointLabelToIndex
  , pointsToShowLabelsFor
  , fullyMappedNetwork
};