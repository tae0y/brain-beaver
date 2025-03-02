// refer to https://cosmograph.app/docs/cosmograph/Introduction

import './style.css';
import { onDataReady, pointPositions, links, pointColors, pointSizes, linkColors, linkWidths } from './data-gen';
import { Graph, GraphConfigInterface } from '@cosmograph/cosmos';

onDataReady(initGraph);

function initGraph(){
  const div = document.getElementById('graph') as HTMLDivElement;
  let graph: Graph;
  const config: GraphConfigInterface = {
    spaceSize: 4096,
    pointSize: 10,
    pointGreyoutOpacity: 0.1,
    //pointColor: '#2748A4',
    //linkColor: '#88C6FF',
    linkArrows: false,
    linkGreyoutOpacity: 0,
    curvedLinks: true,
    backgroundColor: '#151515',
    renderHoveredPointRing: true,
    hoveredPointRingColor: '#4B5BBF',
    enableDrag: true,
    simulationFriction: 0.1,
    simulationLinkDistance: 20,
    simulationLinkSpring: 2,
    simulationRepulsion: 0.5,
    simulationGravity: 0.1,
    simulationDecay: 100000,
    fitViewPadding: 0.3,
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
  graph.setPointColors(pointColors);
  graph.setPointSizes(pointSizes);
  graph.setLinks(links);
  graph.setLinkColors(linkColors);
  graph.setLinkWidths(linkWidths);

  //graph.zoom(0.9);
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
  
  //function selectPointsInArea() {
  //  const w = canvas.clientWidth;
  //  const h = canvas.clientHeight;
  //  const left = getRandomInRange([w / 4, w / 2]);
  //  const right = getRandomInRange([left, (w * 3) / 4]);
  //  const top = getRandomInRange([h / 4, h / 2]);
  //  const bottom = getRandomInRange([top, (h * 3) / 4]);
  //  pause();
  //  graph.selectPointsInRange([
  //    [left, top],
  //    [right, bottom],
  //  ]);
  //}
  
  document.getElementById('fit-view')?.addEventListener('click', fitView);
  document.getElementById('zoom')?.addEventListener('click', zoomIn);
  document.getElementById('select-point')?.addEventListener('click', selectPoint);
  //document
  //  .getElementById('select-points-in-area')
  //  ?.addEventListener('click', selectPointsInArea);
}