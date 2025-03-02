// refer to https://cosmograph.app/docs/cosmograph/Introduction

import './style.css';
import { 
  onDataReady, // async callback subscription
  pointPositions, pointColors, pointSizes,  //point
  links, linkColors, linkWidths, fullyMappedNetwork,  //link
  pointIndexToLabel, pointLabelToIndex, pointsToShowLabelsFor, //label
} from './data-gen';
import { CosmosLabels } from './labels';
import { Graph, GraphConfigInterface } from '@cosmograph/cosmos';

onDataReady(initGraph);

function initGraph(){
  // ------------------------------------------------------------------------------
  // 화면 초기설정
  const appDiv = document.getElementsByClassName('app')[0];

  const labelsDiv = document.createElement('div');
  labelsDiv.className = 'labels';
  appDiv.appendChild(labelsDiv)

  const graphDiv = document.createElement('div')
  graphDiv.className = 'graph'
  appDiv.appendChild(graphDiv)


  // ------------------------------------------------------------------------------
  // 라벨 뷰
  const cosmosLabels = new CosmosLabels(labelsDiv, pointIndexToLabel)


  // ------------------------------------------------------------------------------
  // 그래프 뷰
  let graph: Graph;
  const config: GraphConfigInterface = {
    spaceSize: 4096,
    backgroundColor: '#2d313a',
    linkWidth: 0.1,
    linkColor: '#5F74C2',
    linkArrows: false,
    fitViewOnInit: true,
    enableDrag: true,
    simulationGravity: 0.1,
    simulationLinkDistance: 1,
    simulationLinkSpring: 0.3,
    simulationRepulsion: 0.4,
    onSimulationTick: () => graph && cosmosLabels.update(graph),
    onZoom: () => graph && cosmosLabels.update(graph),
    onClick: (
      index: number | undefined,
      pointPosition: [number, number] | undefined,
      event: MouseEvent
    ) => {
      if (index !== undefined) {
        graph.selectPointByIndex(index);
        graph.zoomToPointByIndex(index);
      } else {
        graph.unselectPoints();
      }
      console.log('Clicked point index: ', index);
    },
  };

  graph = new Graph(graphDiv, config);
  graph.setPointPositions(pointPositions);
  graph.setPointColors(pointColors);
  graph.setPointSizes(pointSizes);
  graph.setLinks(links);
  graph.setLinkColors(linkColors);
  graph.setLinkWidths(linkWidths);
  graph.render(0.1);
  graph.trackPointPositionsByIndices(
    pointsToShowLabelsFor.map(
      label => {
        return pointLabelToIndex.get(`${label}`) as number;
      }
    )
  )
  setTimeout(()=>{
    graph.pause();
  },2000)

  /* ~ Demo Actions ~ */
  // Start / Pause
  let isPaused = false;
  const pauseButton = document.getElementById('pause') as HTMLDivElement;

  function pause() {
    isPaused = true;
    pauseButton.textContent = 'Start';
    graph.pause();
  }

  function start() {
    isPaused = false;
    pauseButton.textContent = 'Pause';
    graph.start();
  }

  function togglePause() {
    if (isPaused) start();
    else pause();
  }

  pauseButton.addEventListener('click', togglePause);

  // Zoom and Select
  function getRandomPointIndex() {
    return Math.floor((Math.random() * pointPositions.length) / 2);
  }

  function getRandomInRange([min, max]: [number, number]): number {
    return Math.random() * (max - min) + min;
  }

  function fitView() {
    graph.fitView();
  }

  function zoomIn() {
    const pointIndex = getRandomPointIndex();
    graph.zoomToPointByIndex(pointIndex);
    graph.selectPointByIndex(pointIndex);
    pause();
  }

  function selectPoint() {
    const pointIndex = getRandomPointIndex();
    graph.selectPointByIndex(pointIndex);
    graph.fitView();
    pause();
  }

  function selectPointsInArea() {
    const w = appDiv.clientWidth;
    const h = appDiv.clientHeight;
    const left = getRandomInRange([w / 4, w / 2]);
    const right = getRandomInRange([left, (w * 3) / 4]);
    const top = getRandomInRange([h / 4, h / 2]);
    const bottom = getRandomInRange([top, (h * 3) / 4]);
    pause();
    graph.selectPointsInRange([
      [left, top],
      [right, bottom],
    ]);
  }

  function selectMostLinkedPoint(){
    graph.zoomToPointByIndex(pointLabelToIndex.get(`${pointsToShowLabelsFor[0]}`) ?? -1);
    graph.selectPointByIndex(pointLabelToIndex.get(`${pointsToShowLabelsFor[0]}`) ?? -1);
  }

  function selectMostLinkedNetwork(){
    graph.fitView();
    const rootIndex = Math.floor(Math.random()*pointsToShowLabelsFor.length);
    const root = pointsToShowLabelsFor[rootIndex];
    graph.selectPointsByIndices(
      fullyMappedNetwork.get(root) ?? []
    )
    graph.zoomToPointByIndex(pointLabelToIndex.get(`${root}`) ?? -1);
  }

  document.getElementById('fit-view')?.addEventListener('click', fitView);
  document.getElementById('zoom')?.addEventListener('click', zoomIn);
  document.getElementById('select-point')?.addEventListener('click', selectPoint);
  document.getElementById('select-points-in-area')?.addEventListener('click', selectPointsInArea);
  document.getElementById('select-most-linked-point')?.addEventListener('click', selectMostLinkedPoint);
  document.getElementById('select-most-linked-network')?.addEventListener('click', selectMostLinkedNetwork);

}