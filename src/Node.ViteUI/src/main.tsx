// cosmos v1 : https://cosmograph.app/docs/cosmograph/Introduction
// cosmos v2 : https://cosmograph-org.github.io/cosmos/?path=/docs/welcome-to-cosmos--docs
import { createRoot } from 'react-dom/client';
import VaulDrawer from './drawer';
import { useLoading, LoaderProvider, Grid } from '@agney/react-loading'
import React, { useState, useEffect } from 'react';
import './style.css';
import { 
  onDataReady, // async callback subscription
  pointPositions, pointColors, pointSizes, conceptsRawDataList, //point
  links, linkColors, linkWidths, fullyMappedNetwork,  //link
  pointIndexToLabel, pointLabelToIndex, pointsToShowLabelsFor, //label
} from './data-gen';
import { CosmosLabels } from './labels';
import { Graph, GraphConfigInterface } from '@cosmograph/cosmos';


/*********************************************************************************************
 * 
 * Dom
 * 
 * 
 *********************************************************************************************/

function App() {
  const [loading, setLoading] = useState(true);
  const { containerProps, indicatorEl } = useLoading({ 
    loading: true,
  });
  useEffect(() => {
    onDataReady(() => {
      setLoading(false);
      initGraph();
    });
  }, []);
  return loading ? (
    <section 
      {...containerProps}>
        {indicatorEl}
    </section>
  ) : null;
}

// ------------------------------------------------------------------------------
// 화면 초기설정
const appDiv = document.getElementsByClassName('app')[0];

const loaderDiv = document.createElement('div');
loaderDiv.className = 'loader';
appDiv.appendChild(loaderDiv);
const loaderRoot = createRoot(loaderDiv)
loaderRoot.render(
  <LoaderProvider indicator={<Grid />}>
    <App />
  </LoaderProvider>
);

const labelsDiv = document.createElement('div');
labelsDiv.className = 'labels';
appDiv.appendChild(labelsDiv)

const graphDiv = document.createElement('div')
graphDiv.className = 'graph'
appDiv.appendChild(graphDiv)

const drawerContainer = document.createElement('div');
drawerContainer.id = 'drawer-root';
document.body.appendChild(drawerContainer);
const drawerRoot = createRoot(drawerContainer);


/*********************************************************************************************
 * 
 * Graph
 * 
 * 
 *********************************************************************************************/
//onDataReady(initGraph);

function initGraph(){
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
    linkArrows: true,
    fitViewOnInit: true,
    enableDrag: true,
    renderHoveredPointRing: true,
    hoveredPointRingColor: '#FFFF00',
    simulationGravity: 0.002,
    simulationLinkDistance: 1,
    simulationLinkSpring: 0.3,
    simulationRepulsion: 0.5,
    simulationDecay: 3000,
    useQuadtree: true,
    onSimulationStart() {
        console.log('Simulation started');
    },
    onSimulationEnd() {
        console.log('Simulation ended');
    },
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

        // Drawer 렌더링
        drawerRoot.render(
          <VaulDrawer 
            title={conceptsRawDataList[index].title}
            keywords={conceptsRawDataList[index].keywords.replaceAll('{', '').replaceAll('}', '').replaceAll('"', '').replaceAll('\'', '')}
            data_name={conceptsRawDataList[index].data_name}
            summary={conceptsRawDataList[index].summary}
            isOpen={true}
            onOpenChange={(open) => {
              if (!open) {
                drawerRoot.render(null);
              }
            }}
          />
        );
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
  const trackIndices = pointsToShowLabelsFor.map( label => { return pointLabelToIndex.get(`${label}`) as number; } );
  graph.trackPointPositionsByIndices(trackIndices);
  setTimeout(()=>{
    //graph.fitView();
  },10000)


  // ------------------------------------------------------------------------------
  // Start / Pause
  const pauseButton = document.getElementById('pause') as HTMLDivElement;
  pauseButton.addEventListener('click', togglePause);

  let isPaused = false;
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

  // Zoom and Select
  document.getElementById('fit-view')?.addEventListener('click', fitView);
  document.getElementById('zoom')?.addEventListener('click', zoomIn);
  document.getElementById('select-point')?.addEventListener('click', selectPoint);
  document.getElementById('select-points-in-area')?.addEventListener('click', selectPointsInArea);
  document.getElementById('select-most-linked-point')?.addEventListener('click', selectMostLinkedPoint);
  document.getElementById('select-most-linked-network')?.addEventListener('click', selectMostLinkedNetwork);

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
    const rootLabelIndex = Math.floor(Math.random()*pointsToShowLabelsFor.length);
    const rootLabel = pointsToShowLabelsFor[rootLabelIndex];
    const rootPoint = pointLabelToIndex.get(rootLabel) ?? -1;
    graph.selectPointsByIndices(
      fullyMappedNetwork.get(`${rootPoint}`) ?? []
    )
    graph.zoomToPointByIndex(rootPoint);
  }


}