// refer to https://cosmograph.app/docs/cosmograph/Introduction

import './style.css';
import { pointPositions, links, onDataReady } from './data-gen';
import { Cosmograph } from '@cosmograph/cosmograph'
import { Graph, GraphConfigInterface } from '@cosmograph/cosmos';

onDataReady(initGraph);

const colors = ['#88C6FF', '#FF99D2', '#2748A4'];

function initGraph(){
  const div = document.getElementById('graph') as HTMLDivElement;
  document.body.appendChild(div);
  const graph = new Cosmograph(div)

  const config = {
    renderHoveredPointRing: true,
    hoveredNodeRingColor:'red',
    focusedNodeRingColor: 'yellow', 
    showDynamicLabels: true,
    nodeSize: 1,
    nodeColor: () => colors[Math.floor(Math.random() * colors.length)],
    linkWidth: () => 1 + 2 * Math.random(),
    linkColor: () => colors[Math.floor(Math.random() * colors.length)],
    spaceSize: 4096,
    backgroundColor: '#151515',
    pointGreyoutOpacity: 0.1,
    linkArrows: false,
    linkGreyoutOpacity: 0,
    curvedLinks: true,
    enableDrag: true,
    simulationFriction: 0.1,
    simulationLinkSpring: 0.5, 
    simulationLinkDistance: 2.0,
    simulationRepulsion: 0.2,
    simulationGravity: 0.1,
    simulationDecay: 100000
  }

  graph.setConfig(config)
  graph.setData(pointPositions, links)
  
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
}