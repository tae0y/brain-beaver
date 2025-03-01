import './style.css';
import { pointPositions, links } from './data-gen';
import { Graph, GraphConfigInterface } from '@cosmograph/cosmos';

const div = document.getElementById('graph') as HTMLDivElement;
let graph: Graph;
const config: GraphConfigInterface = {
  spaceSize: 4096,
  backgroundColor: '#151515',
  pointSize: 4,
  pointColor: '#4B5BBF',
  pointGreyoutOpacity: 0.1,
  linkWidth: 0.1,
  linkColor: '#5F74C2',
  linkArrows: false,
  linkGreyoutOpacity: 0,
  curvedLinks: true,
  renderHoveredPointRing: true,
  hoveredPointRingColor: '#4B5BBF',
  enableDrag: true,
  simulationLinkDistance: 1,
  simulationLinkSpring: 2,
  simulationRepulsion: 0.2,
  simulationGravity: 0.1,
  simulationDecay: 100000,
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

graph = new Graph(div, config);
graph.setPointPositions(pointPositions);
graph.setLinks(links);

graph.zoom(0.9);
graph.render();

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
  const w = canvas.clientWidth;
  const h = canvas.clientHeight;
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

document.getElementById('fit-view')?.addEventListener('click', fitView);
document.getElementById('zoom')?.addEventListener('click', zoomIn);
document.getElementById('select-point')?.addEventListener('click', selectPoint);
document
  .getElementById('select-points-in-area')
  ?.addEventListener('click', selectPointsInArea);
