import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import ConfirmDialog from './confirm-dialog';

interface Document {
  id: number;
  title: string;
  data_name: string;
  create_time: string;
}

interface Concept {
  id: number;
  title: string;
  keywords: string;
  category: string;
  summary: string;
  data_name: string;
  create_time: string;
}

export default function AdminPanel() {
  const [dataSourceType, setDataSourceType] = useState<'markdown' | 'website'>('markdown');
  const [websiteUrl, setWebsiteUrl] = useState('');
  const [markdownFiles, setMarkdownFiles] = useState<FileList | null>(null);
  const [documents, setDocuments] = useState<Document[]>([]);
  const [concepts, setConcepts] = useState<Concept[]>([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [processingProgress, setProcessingProgress] = useState(0);
  const [processingMessage, setProcessingMessage] = useState('');
  const [selectedItems, setSelectedItems] = useState<Set<number>>(new Set());
  const [currentProcessAbortController, setCurrentProcessAbortController] = useState<AbortController | null>(null);
  const [showDeleteAllDialog, setShowDeleteAllDialog] = useState(false);
  const [showRelationshipMappingDialog, setShowRelationshipMappingDialog] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    loadDocuments();
    loadConcepts();
  }, []);

  const loadDocuments = async () => {
    try {
      // This would need a new API endpoint to get documents
      // For now using concepts as documents proxy
      const response = await axios.get('http://localhost:8112/api/concepts');
      if (response.data.status === 'success') {
        setDocuments(response.data.data.map((concept: Concept) => ({
          id: concept.id,
          title: concept.data_name,
          data_name: concept.data_name,
          create_time: concept.create_time
        })));
      }
    } catch (error) {
      console.error('Failed to load documents:', error);
    }
  };

  const loadConcepts = async () => {
    try {
      const response = await axios.get('http://localhost:8112/api/concepts');
      if (response.data.status === 'success') {
        setConcepts(response.data.data);
      }
    } catch (error) {
      console.error('Failed to load concepts:', error);
    }
  };

  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files;
    if (files) {
      setMarkdownFiles(files);
    }
  };

  const handleProcessData = async () => {
    if (isProcessing) return;

    const abortController = new AbortController();
    setCurrentProcessAbortController(abortController);
    setIsProcessing(true);
    setProcessingProgress(0);
    setProcessingMessage('Processing data...');

    try {
      let datasourcepath = '';
      
      if (dataSourceType === 'website') {
        datasourcepath = websiteUrl;
      } else {
        // TODO: For markdown files, we'll need to implement file upload to server
        // For now, simulate with a path
        datasourcepath = '/uploaded/markdown/path';
      }

      const options = {
        max_budget: 10000,
        max_file_num: 10,
        shuffle_flag: true
      };

      // Simulate progress updates
      const progressInterval = setInterval(() => {
        setProcessingProgress(prev => {
          if (prev >= 90) {
            clearInterval(progressInterval);
            return prev;
          }
          return prev + Math.random() * 10;
        });
      }, 1000);

      // Start extraction
      const response = await axios.post('http://localhost:8112/api/extract', {
        datasourcetype: dataSourceType,
        datasourcepath,
        options
      }, {
        signal: abortController.signal
      });

      clearInterval(progressInterval);

      if (response.data.status === 'success') {
        setProcessingMessage('Data extraction completed successfully');
        setProcessingProgress(100);
        await loadDocuments();
        await loadConcepts();
      }
    } catch (error) {
      if (axios.isCancel(error)) {
        setProcessingMessage('Processing cancelled');
      } else {
        console.error('Processing failed:', error);
        setProcessingMessage('Processing failed');
      }
    } finally {
      setCurrentProcessAbortController(null);
      setTimeout(() => {
        setIsProcessing(false);
        setProcessingProgress(0);
        setProcessingMessage('');
      }, 2000);
    }
  };

  const handleCancelProcessing = () => {
    if (currentProcessAbortController) {
      currentProcessAbortController.abort();
    }
  };

  const handleRelationshipMapping = async () => {
    if (isProcessing) return;
    setShowRelationshipMappingDialog(true);
  };

  const confirmRelationshipMapping = async () => {
    setShowRelationshipMappingDialog(false);
    setIsProcessing(true);
    setProcessingProgress(0);
    setProcessingMessage('Creating relationship mappings...');

    try {
      const options = {
        operation: 'cosine_distance',
        cosine_sim_check: true
      };

      const response = await axios.post('http://localhost:8112/api/networks/engage', options);

      if (response.data.status === 'success') {
        setProcessingMessage('Relationship mapping completed');
        setProcessingProgress(100);
      }
    } catch (error) {
      console.error('Relationship mapping failed:', error);
      setProcessingMessage('Relationship mapping failed');
    } finally {
      setTimeout(() => {
        setIsProcessing(false);
        setProcessingProgress(0);
        setProcessingMessage('');
      }, 2000);
    }
  };

  const handleWebSearchExpansion = async () => {
    if (isProcessing) return;

    setIsProcessing(true);
    setProcessingProgress(0);
    setProcessingMessage('Expanding knowledge with web search...');

    try {
      const options = {
        action_type: 'all'
      };

      const response = await axios.post('http://localhost:8112/api/references/expand', options);

      if (response.data.status === 'success') {
        setProcessingMessage('Web search expansion completed');
        setProcessingProgress(100);
      }
    } catch (error) {
      console.error('Web search expansion failed:', error);
      setProcessingMessage('Web search expansion failed');
    } finally {
      setTimeout(() => {
        setIsProcessing(false);
        setProcessingProgress(0);
        setProcessingMessage('');
      }, 2000);
    }
  };

  const handleDeleteConcept = async (conceptId: number) => {
    if (isProcessing) return;
    // Note: There's no individual delete endpoint, only delete all
    // This would need to be implemented in the backend
    console.log('Delete concept:', conceptId);
  };

  const handleDeleteAllConcepts = async () => {
    if (isProcessing) return;
    setShowDeleteAllDialog(true);
  };

  const confirmDeleteAllConcepts = async () => {
    setShowDeleteAllDialog(false);
    
    try {
      await axios.delete('http://localhost:8112/api/concepts');
      await loadConcepts();
    } catch (error) {
      console.error('Failed to delete concepts:', error);
    }
  };

  const toggleSelectAll = () => {
    if (selectedItems.size === concepts.length) {
      setSelectedItems(new Set());
    } else {
      setSelectedItems(new Set(concepts.map(c => c.id)));
    }
  };

  const toggleSelectItem = (id: number) => {
    const newSelected = new Set(selectedItems);
    if (newSelected.has(id)) {
      newSelected.delete(id);
    } else {
      newSelected.add(id);
    }
    setSelectedItems(newSelected);
  };

  const goToKnowledgeGraph = () => {
    window.location.href = '/';
  };

  return (
    <div className="admin-panel">
      <header className="admin-header">
        <h1>BrainBeaver 관리자</h1>
        <button onClick={goToKnowledgeGraph} className="nav-button">
          지식그래프 보기
        </button>
      </header>

      {isProcessing && (
        <div className="processing-bar">
          <div className="progress-container">
            <div className="progress-bar" style={{ width: `${processingProgress}%` }}></div>
          </div>
          <div className="processing-info">
            <span>{processingMessage}</span>
            <button 
              onClick={handleCancelProcessing} 
              className="cancel-button"
              disabled={!currentProcessAbortController}
            >
              취소
            </button>
          </div>
        </div>
      )}

      <main className="admin-content">
        <section className="upload-section">
          <h2>데이터 업로드</h2>
          
          <div className="data-source-selector">
            <label>
              <input
                type="radio"
                value="markdown"
                checked={dataSourceType === 'markdown'}
                onChange={(e) => setDataSourceType(e.target.value as 'markdown')}
                disabled={isProcessing}
              />
              마크다운 파일
            </label>
            <label>
              <input
                type="radio"
                value="website"
                checked={dataSourceType === 'website'}
                onChange={(e) => setDataSourceType(e.target.value as 'website')}
                disabled={isProcessing}
              />
              웹사이트 URL
            </label>
          </div>

          {dataSourceType === 'markdown' && (
            <div className="file-upload">
              <input
                type="file"
                ref={fileInputRef}
                onChange={handleFileUpload}
                multiple
                accept=".md,.markdown"
                disabled={isProcessing}
              />
              {markdownFiles && (
                <p>{markdownFiles.length} 파일이 선택됨</p>
              )}
            </div>
          )}

          {dataSourceType === 'website' && (
            <div className="url-input">
              <input
                type="url"
                value={websiteUrl}
                onChange={(e) => setWebsiteUrl(e.target.value)}
                placeholder="https://example.com"
                disabled={isProcessing}
              />
            </div>
          )}

          <button 
            onClick={handleProcessData}
            disabled={isProcessing || (dataSourceType === 'website' && !websiteUrl) || (dataSourceType === 'markdown' && !markdownFiles)}
            className="process-button"
          >
            데이터 처리
          </button>
        </section>

        <section className="document-section">
          <h2>업로드된 문서 ({documents.length}개)</h2>
          <div className="document-list">
            {documents.map((doc) => (
              <div key={doc.id} className="document-item">
                <span>{doc.title}</span>
                <span>{doc.create_time}</span>
              </div>
            ))}
          </div>
        </section>

        <section className="concept-section">
          <h2>지식 단위 ({concepts.length}개)</h2>
          
          <div className="concept-controls">
            <button onClick={toggleSelectAll} disabled={isProcessing}>
              {selectedItems.size === concepts.length ? '전체 해제' : '전체 선택'}
            </button>
            <button onClick={handleDeleteAllConcepts} disabled={isProcessing}>
              전체 삭제
            </button>
            <button onClick={handleRelationshipMapping} disabled={isProcessing || concepts.length === 0}>
              연관관계 매핑
            </button>
            <button onClick={handleWebSearchExpansion} disabled={isProcessing || concepts.length === 0}>
              웹검색 확장
            </button>
          </div>

          <div className="concept-list">
            {concepts.map((concept) => (
              <div key={concept.id} className="concept-item">
                <input
                  type="checkbox"
                  checked={selectedItems.has(concept.id)}
                  onChange={() => toggleSelectItem(concept.id)}
                  disabled={isProcessing}
                />
                <div className="concept-info">
                  <h4>{concept.title}</h4>
                  <p>키워드: {concept.keywords}</p>
                  <p>카테고리: {concept.category}</p>
                  <p>데이터명: {concept.data_name}</p>
                  <p className="summary">{concept.summary}</p>
                </div>
                <button 
                  onClick={() => handleDeleteConcept(concept.id)}
                  disabled={isProcessing}
                  className="delete-button"
                >
                  삭제
                </button>
              </div>
            ))}
          </div>
        </section>
      </main>

      <ConfirmDialog
        isOpen={showDeleteAllDialog}
        title="전체 삭제 확인"
        message="모든 지식 단위를 삭제하시겠습니까? 이 작업은 되돌릴 수 없습니다."
        confirmText="삭제"
        cancelText="취소"
        confirmButtonStyle="danger"
        onConfirm={confirmDeleteAllConcepts}
        onCancel={() => setShowDeleteAllDialog(false)}
      />

      <ConfirmDialog
        isOpen={showRelationshipMappingDialog}
        title="연관관계 매핑 확인"
        message="지식 단위들 간의 연관관계를 매핑하시겠습니까? 기존 연관관계는 초기화될 수 있습니다."
        confirmText="진행"
        cancelText="취소"
        confirmButtonStyle="primary"
        onConfirm={confirmRelationshipMapping}
        onCancel={() => setShowRelationshipMappingDialog(false)}
      />
    </div>
  );
}