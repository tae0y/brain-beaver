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

interface Reference {
  id: number;
  concept_id: number;
  description: string;
  concept?: Concept;
}

interface ParsedDescription {
  counterArgument: string;
  finalReview: string;
  webSearchResults: Array<{
    persona: string;
    decision: string;
    detailed: string;
  }>;
}

export default function AdminPanel() {
  const [dataSourceType, setDataSourceType] = useState<'markdown' | 'website'>('markdown');
  const [websiteUrl, setWebsiteUrl] = useState('');
  const [markdownFiles, setMarkdownFiles] = useState<FileList | null>(null);
  const [documents, setDocuments] = useState<Document[]>([]);
  const [concepts, setConcepts] = useState<Concept[]>([]);
  const [references, setReferences] = useState<Reference[]>([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [processingProgress, setProcessingProgress] = useState(0);
  const [processingMessage, setProcessingMessage] = useState('');
  const [selectedItems, setSelectedItems] = useState<Set<number>>(new Set());
  const [selectedReferences, setSelectedReferences] = useState<Set<number>>(new Set());
  const [currentProcessAbortController, setCurrentProcessAbortController] = useState<AbortController | null>(null);
  const [showDeleteAllDialog, setShowDeleteAllDialog] = useState(false);
  const [showDeleteAllReferencesDialog, setShowDeleteAllReferencesDialog] = useState(false);
  const [showRelationshipMappingDialog, setShowRelationshipMappingDialog] = useState(false);
  
  // Search and filter states
  const [conceptSearch, setConceptSearch] = useState('');
  const [conceptCategoryFilter, setConceptCategoryFilter] = useState('');
  const [conceptDataNameFilter, setConceptDataNameFilter] = useState('');
  const [referenceSearch, setReferenceSearch] = useState('');
  const [referenceDecisionFilter, setReferenceDecisionFilter] = useState('');
  const [referenceConceptFilter, setReferenceConceptFilter] = useState('');
  
  // Applied filter states (what's actually being used for filtering)
  const [appliedConceptSearch, setAppliedConceptSearch] = useState('');
  const [appliedConceptCategoryFilter, setAppliedConceptCategoryFilter] = useState('');
  const [appliedConceptDataNameFilter, setAppliedConceptDataNameFilter] = useState('');
  const [appliedReferenceSearch, setAppliedReferenceSearch] = useState('');
  const [appliedReferenceDecisionFilter, setAppliedReferenceDecisionFilter] = useState('');
  const [appliedReferenceConceptFilter, setAppliedReferenceConceptFilter] = useState('');
  
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    loadDocuments();
    loadConcepts();
    loadReferences();
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

  const loadReferences = async () => {
    try {
      const response = await axios.get('http://localhost:8112/api/references');
      if (response.data.status === 'success') {
        const referencesWithConcepts = response.data.data.map((ref: Reference) => {
          const concept = concepts.find(c => c.id === ref.concept_id);
          return { ...ref, concept };
        });
        setReferences(referencesWithConcepts);
      }
    } catch (error) {
      console.error('Failed to load references:', error);
    }
  };

  // Reload references when concepts change to populate concept data
  useEffect(() => {
    if (concepts.length > 0) {
      loadReferences();
    }
  }, [concepts]);

  const normalizeJsonString = (jsonStr: string): string => {
    // Remove any leading/trailing whitespace
    let normalized = jsonStr.trim();
    
    // Handle edge case where the string might be wrapped in quotes
    if ((normalized.startsWith('"') && normalized.endsWith('"')) ||
        (normalized.startsWith("'") && normalized.endsWith("'"))) {
      normalized = normalized.slice(1, -1);
    }
    
    // Replace problematic quotes step by step
    // 1. First, protect content inside double quotes (if any)
    let protectedStrings: string[] = [];
    let stringIndex = 0;
    
    // Protect existing double-quoted strings
    normalized = normalized.replace(/"([^"\\\\]*(\\\\.[^"\\\\]*)*)"/g, (match) => {
      const placeholder = `___STRING_${stringIndex++}___`;
      protectedStrings.push(match);
      return placeholder;
    });
    
    // 2. Now handle single-quoted strings - convert them to double quotes
    normalized = normalized.replace(/'([^'\\\\]*(\\\\.[^'\\\\]*)*)'/g, (match, content) => {
      const placeholder = `___STRING_${stringIndex++}___`;
      // Convert single quotes to double quotes and escape internal double quotes
      const escaped = content.replace(/"/g, '\\"');
      protectedStrings.push(`"${escaped}"`);
      return placeholder;
    });
    
    // 3. Replace any remaining single quotes with double quotes (these should be structural)
    normalized = normalized.replace(/'/g, '"');
    
    // 4. Restore protected strings
    for (let i = protectedStrings.length - 1; i >= 0; i--) {
      normalized = normalized.replace(`___STRING_${i}___`, protectedStrings[i]);
    }
    
    // Fix common JSON formatting issues
    normalized = normalized
      // Remove trailing commas before closing brackets/braces
      .replace(/,(\s*[}\]])/g, '$1')
      // Fix spacing issues
      .replace(/:\s*/g, ':')
      .replace(/,\s*/g, ',')
      // Remove any invalid commas at the start
      .replace(/\[\s*,/g, '[')
      .replace(/{\s*,/g, '{')
      // Fix boolean values
      .replace(/:\s*True\b/g, ': true')
      .replace(/:\s*False\b/g, ': false')
      .replace(/:\s*None\b/g, ': null');
    
    return normalized;
  };

  const parseDescription = (description: string): ParsedDescription => {
    const parts = description.split('//').map(part => part.trim());
    
    let counterArgument = '';
    let finalReview = '';
    let webSearchResults: ParsedDescription['webSearchResults'] = [];

    parts.forEach(part => {
      if (part.startsWith('악마의대변인')) {
        counterArgument = part.replace(/^악마의대변인\s*:?\s*/, '').trim();
      } else if (part.startsWith('최종검토의견')) {
        finalReview = part.replace(/^최종검토의견\s*:?\s*/, '').trim();
      } else if (part.startsWith('관련근거문서')) {
        try {
          let jsonStr = part.replace(/^관련근거문서\s*:?\s*/, '').trim();
          
          // Log original string for debugging
          console.log('Original JSON string (first 300 chars):', jsonStr.substring(0, 300) + '...');
          
          // Apply normalization
          jsonStr = normalizeJsonString(jsonStr);
          
          console.log('Normalized JSON string (first 300 chars):', jsonStr.substring(0, 300) + '...');
          
          const parsed = JSON.parse(jsonStr);
          webSearchResults = Array.isArray(parsed) ? parsed : [];
          
          console.log('Successfully parsed web search results:', webSearchResults.length, 'items');
        } catch (error) {
          console.error('Primary parsing failed:', error);
          console.error('Problematic JSON string (first 500 chars):', part.substring(0, 500) + '...');
          
          // Try multiple alternative parsing approaches
          let success = false;
          
          // Method 1: Extract array pattern with regex
          if (!success) {
            try {
              const arrayMatch = part.match(/\[[\s\S]*\]/);
              if (arrayMatch) {
                let extractedJson = arrayMatch[0];
                extractedJson = normalizeJsonString(extractedJson);
                console.log('Attempting regex extraction method 1...');
                const parsed = JSON.parse(extractedJson);
                webSearchResults = Array.isArray(parsed) ? parsed : [];
                console.log('Successfully parsed with regex method 1:', webSearchResults.length, 'items');
                success = true;
              }
            } catch (regexError) {
              console.error('Regex method 1 failed:', regexError);
            }
          }
          
          // Method 2: More aggressive string cleaning
          if (!success) {
            try {
              let cleanStr = part.replace(/^관련근거문서\s*:?\s*/, '').trim();
              
              // Remove any non-JSON prefix/suffix
              const startIdx = cleanStr.indexOf('[');
              const endIdx = cleanStr.lastIndexOf(']');
              
              if (startIdx !== -1 && endIdx !== -1 && endIdx > startIdx) {
                cleanStr = cleanStr.substring(startIdx, endIdx + 1);
                cleanStr = normalizeJsonString(cleanStr);
                console.log('Attempting aggressive cleaning method...');
                const parsed = JSON.parse(cleanStr);
                webSearchResults = Array.isArray(parsed) ? parsed : [];
                console.log('Successfully parsed with aggressive cleaning:', webSearchResults.length, 'items');
                success = true;
              }
            } catch (cleanError) {
              console.error('Aggressive cleaning method failed:', cleanError);
            }
          }
          
          // Method 3: Manual parsing as fallback
          if (!success) {
            try {
              console.log('Attempting manual parsing fallback...');
              // Look for persona/decision/detailed patterns
              const manualResults = [];
              const personaMatches = part.matchAll(/'persona':\s*'([^']*?)'/g);
              const decisionMatches = part.matchAll(/'decision':\s*'([^']*?)'/g);
              const detailedMatches = part.matchAll(/'detailed':\s*'([^']*?)'/g);
              
              const personas = Array.from(personaMatches, m => m[1]);
              const decisions = Array.from(decisionMatches, m => m[1]);
              const detaileds = Array.from(detailedMatches, m => m[1]);
              
              for (let i = 0; i < Math.max(personas.length, decisions.length, detaileds.length); i++) {
                manualResults.push({
                  persona: personas[i] || '',
                  decision: decisions[i] || '',
                  detailed: detaileds[i] || ''
                });
              }
              
              if (manualResults.length > 0) {
                webSearchResults = manualResults;
                console.log('Successfully parsed with manual fallback:', webSearchResults.length, 'items');
                success = true;
              }
            } catch (manualError) {
              console.error('Manual parsing fallback failed:', manualError);
            }
          }
          
          if (!success) {
            console.error('All parsing methods failed, setting empty results');
            webSearchResults = [];
          }
        }
      }
    });

    return { counterArgument, finalReview, webSearchResults };
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

  const handleDeleteAllReferences = async () => {
    if (isProcessing) return;
    setShowDeleteAllReferencesDialog(true);
  };

  const confirmDeleteAllReferences = async () => {
    setShowDeleteAllReferencesDialog(false);
    
    try {
      await axios.delete('http://localhost:8112/api/references');
      await loadReferences();
    } catch (error) {
      console.error('Failed to delete references:', error);
    }
  };

  const handleDeleteReference = async (referenceId: number) => {
    if (isProcessing) return;
    // Note: Backend doesn't have individual delete endpoint for references
    // This would need to be implemented
    console.log('Delete reference:', referenceId);
  };

  const toggleSelectAll = () => {
    if (selectedItems.size === filteredConcepts.length && filteredConcepts.length > 0) {
      setSelectedItems(new Set());
    } else {
      setSelectedItems(new Set(filteredConcepts.map(c => c.id)));
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

  const toggleSelectAllReferences = () => {
    if (selectedReferences.size === filteredReferences.length && filteredReferences.length > 0) {
      setSelectedReferences(new Set());
    } else {
      setSelectedReferences(new Set(filteredReferences.map(r => r.id)));
    }
  };

  const toggleSelectReference = (id: number) => {
    const newSelected = new Set(selectedReferences);
    if (newSelected.has(id)) {
      newSelected.delete(id);
    } else {
      newSelected.add(id);
    }
    setSelectedReferences(newSelected);
  };

  // Filter functions using applied states
  const filteredConcepts = concepts.filter(concept => {
    // If no applied filters, show nothing (user must explicitly search)
    if (!appliedConceptSearch && !appliedConceptCategoryFilter && !appliedConceptDataNameFilter) {
      return false;
    }
    
    // Special case: show all when marked with '*'
    if (appliedConceptSearch === '*') {
      return true;
    }
    
    const matchesSearch = appliedConceptSearch === '' || 
      concept.title.toLowerCase().includes(appliedConceptSearch.toLowerCase()) ||
      concept.keywords.toLowerCase().includes(appliedConceptSearch.toLowerCase()) ||
      concept.summary.toLowerCase().includes(appliedConceptSearch.toLowerCase());
    
    const matchesCategory = appliedConceptCategoryFilter === '' || 
      concept.category.toLowerCase().includes(appliedConceptCategoryFilter.toLowerCase());
    
    const matchesDataName = appliedConceptDataNameFilter === '' || 
      concept.data_name.toLowerCase().includes(appliedConceptDataNameFilter.toLowerCase());
    
    return matchesSearch && matchesCategory && matchesDataName;
  });

  const filteredReferences = references.filter(reference => {
    // If no applied filters, show nothing (user must explicitly search)
    if (!appliedReferenceSearch && !appliedReferenceDecisionFilter && !appliedReferenceConceptFilter) {
      return false;
    }
    
    // Special case: show all when marked with '*'
    if (appliedReferenceSearch === '*') {
      return true;
    }
    
    const parsed = parseDescription(reference.description);
    
    const matchesSearch = appliedReferenceSearch === '' || 
      reference.description.toLowerCase().includes(appliedReferenceSearch.toLowerCase()) ||
      parsed.counterArgument.toLowerCase().includes(appliedReferenceSearch.toLowerCase()) ||
      parsed.finalReview.toLowerCase().includes(appliedReferenceSearch.toLowerCase()) ||
      parsed.webSearchResults.some(result => 
        result.persona.toLowerCase().includes(appliedReferenceSearch.toLowerCase()) ||
        result.detailed.toLowerCase().includes(appliedReferenceSearch.toLowerCase())
      );
    
    const matchesDecision = appliedReferenceDecisionFilter === '' ||
      parsed.webSearchResults.some(result => 
        result.decision.toLowerCase() === appliedReferenceDecisionFilter.toLowerCase()
      );
    
    const matchesConcept = appliedReferenceConceptFilter === '' ||
      (reference.concept && 
        reference.concept.title.toLowerCase().includes(appliedReferenceConceptFilter.toLowerCase())
      );
    
    return matchesSearch && matchesDecision && matchesConcept;
  });

  // Get unique values for filter options
  const uniqueCategories = [...new Set(concepts.map(c => c.category).filter(Boolean))];
  const uniqueDataNames = [...new Set(concepts.map(c => c.data_name).filter(Boolean))];
  const uniqueConceptTitles = [...new Set(concepts.map(c => c.title).filter(Boolean))];

  const applyConceptFilters = () => {
    setAppliedConceptSearch(conceptSearch);
    setAppliedConceptCategoryFilter(conceptCategoryFilter);
    setAppliedConceptDataNameFilter(conceptDataNameFilter);
  };

  const applyReferenceFilters = () => {
    setAppliedReferenceSearch(referenceSearch);
    setAppliedReferenceDecisionFilter(referenceDecisionFilter);
    setAppliedReferenceConceptFilter(referenceConceptFilter);
  };

  const clearConceptFilters = () => {
    setConceptSearch('');
    setConceptCategoryFilter('');
    setConceptDataNameFilter('');
    setAppliedConceptSearch('');
    setAppliedConceptCategoryFilter('');
    setAppliedConceptDataNameFilter('');
  };

  const clearReferenceFilters = () => {
    setReferenceSearch('');
    setReferenceDecisionFilter('');
    setReferenceConceptFilter('');
    setAppliedReferenceSearch('');
    setAppliedReferenceDecisionFilter('');
    setAppliedReferenceConceptFilter('');
  };

  // Show all items (remove applied filters but keep input values)
  const showAllConcepts = () => {
    setAppliedConceptSearch('*'); // Use special marker to show all
    setAppliedConceptCategoryFilter('');
    setAppliedConceptDataNameFilter('');
  };

  const showAllReferences = () => {
    setAppliedReferenceSearch('*'); // Use special marker to show all
    setAppliedReferenceDecisionFilter('');
    setAppliedReferenceConceptFilter('');
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
          <h2>지식 단위 (전체: {concepts.length}개, 필터링: {filteredConcepts.length}개)</h2>
          
          <div className="search-filter-section">
            <div className="search-box">
              <input
                type="text"
                placeholder="제목, 키워드, 요약으로 검색..."
                value={conceptSearch}
                onChange={(e) => setConceptSearch(e.target.value)}
                disabled={isProcessing}
                className="search-input"
              />
              <span className="search-icon">🔍</span>
            </div>
            
            <div className="filter-row">
              <select
                value={conceptCategoryFilter}
                onChange={(e) => setConceptCategoryFilter(e.target.value)}
                disabled={isProcessing}
                className="filter-select"
              >
                <option value="">모든 카테고리</option>
                {uniqueCategories.map((category) => (
                  <option key={category} value={category}>{category}</option>
                ))}
              </select>
              
              <select
                value={conceptDataNameFilter}
                onChange={(e) => setConceptDataNameFilter(e.target.value)}
                disabled={isProcessing}
                className="filter-select"
              >
                <option value="">모든 데이터</option>
                {uniqueDataNames.map((dataName) => (
                  <option key={dataName} value={dataName}>{dataName}</option>
                ))}
              </select>
              
              <button 
                onClick={applyConceptFilters} 
                disabled={isProcessing}
                className="search-button"
              >
                검색
              </button>
              
              <button 
                onClick={showAllConcepts} 
                disabled={isProcessing}
                className="show-all-button"
              >
                전체 조회
              </button>
              
              <button 
                onClick={clearConceptFilters} 
                disabled={isProcessing}
                className="clear-filters-button"
              >
                필터 초기화
              </button>
            </div>
          </div>
          
          <div className="concept-controls">
            <button onClick={toggleSelectAll} disabled={isProcessing}>
              {selectedItems.size === filteredConcepts.length && filteredConcepts.length > 0 ? '전체 해제' : '전체 선택'}
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
            {filteredConcepts.length === 0 ? (
              <div className="empty-results">
                검색 조건에 맞는 지식 단위가 없습니다.
              </div>
            ) : (
              filteredConcepts.map((concept) => (
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
              ))
            )}
          </div>
        </section>

        <section className="references-section">
          <h2>웹 검색 참고자료 (전체: {references.length}개, 필터링: {filteredReferences.length}개)</h2>
          
          <div className="search-filter-section">
            <div className="search-box">
              <input
                type="text"
                placeholder="악마의 대변인, 검토의견, 웹검색 결과로 검색..."
                value={referenceSearch}
                onChange={(e) => setReferenceSearch(e.target.value)}
                disabled={isProcessing}
                className="search-input"
              />
              <span className="search-icon">🔍</span>
            </div>
            
            <div className="filter-row">
              <select
                value={referenceDecisionFilter}
                onChange={(e) => setReferenceDecisionFilter(e.target.value)}
                disabled={isProcessing}
                className="filter-select"
              >
                <option value="">모든 결정</option>
                <option value="true">찬성만</option>
                <option value="false">반대만</option>
              </select>
              
              <select
                value={referenceConceptFilter}
                onChange={(e) => setReferenceConceptFilter(e.target.value)}
                disabled={isProcessing}
                className="filter-select"
              >
                <option value="">모든 지식</option>
                {uniqueConceptTitles.map((title) => (
                  <option key={title} value={title}>{title}</option>
                ))}
              </select>
              
              <button 
                onClick={applyReferenceFilters} 
                disabled={isProcessing}
                className="search-button"
              >
                검색
              </button>
              
              <button 
                onClick={showAllReferences} 
                disabled={isProcessing}
                className="show-all-button"
              >
                전체 조회
              </button>
              
              <button 
                onClick={clearReferenceFilters} 
                disabled={isProcessing}
                className="clear-filters-button"
              >
                필터 초기화
              </button>
            </div>
          </div>
          
          <div className="references-controls">
            <button onClick={toggleSelectAllReferences} disabled={isProcessing}>
              {selectedReferences.size === filteredReferences.length && filteredReferences.length > 0 ? '전체 해제' : '전체 선택'}
            </button>
            <button onClick={handleDeleteAllReferences} disabled={isProcessing}>
              전체 삭제
            </button>
          </div>

          <div className="references-list">
            {filteredReferences.length === 0 ? (
              <div className="empty-results">
                검색 조건에 맞는 참고자료가 없습니다.
              </div>
            ) : (
              filteredReferences.map((reference) => {
                const parsed = parseDescription(reference.description);
                return (
                  <div key={reference.id} className="reference-item">
                  <div className="reference-header">
                    <input
                      type="checkbox"
                      checked={selectedReferences.has(reference.id)}
                      onChange={() => toggleSelectReference(reference.id)}
                      disabled={isProcessing}
                    />
                    <div className="reference-concept-info">
                      <h4>관련 지식: {reference.concept?.title || `ID ${reference.concept_id}`}</h4>
                      {reference.concept && (
                        <p className="concept-summary">{reference.concept.summary}</p>
                      )}
                    </div>
                    <button 
                      onClick={() => handleDeleteReference(reference.id)}
                      disabled={isProcessing}
                      className="delete-button"
                    >
                      삭제
                    </button>
                  </div>
                  
                  <div className="reference-content">
                    <div className="counter-argument">
                      <h5>🔥 악마의 대변인</h5>
                      <p>{parsed.counterArgument}</p>
                    </div>
                    
                    <div className="final-review">
                      <h5>📝 최종 검토 의견</h5>
                      <p>{parsed.finalReview}</p>
                    </div>
                    
                    <div className="web-search-results">
                      <h5>🌐 웹 검색 결과 ({parsed.webSearchResults.length}개)</h5>
                      {parsed.webSearchResults.length === 0 && (
                        <div className="parsing-error-info">
                          <p>⚠️ JSON 파싱에 실패했습니다. 개발자 콘솔을 확인해주세요.</p>
                          <details>
                            <summary>원본 데이터 확인</summary>
                            <pre className="raw-data">{reference.description.split('//').find(p => p.includes('관련근거문서'))?.substring(0, 500) + '...'}</pre>
                          </details>
                        </div>
                      )}
                      <div className="search-results-grid">
                        {parsed.webSearchResults.map((result, index) => (
                          <div key={index} className="search-result-item">
                            <div className="result-header">
                              <span className="persona-badge" title={result.persona}>
                                {result.persona.length > 100 ? result.persona.substring(0, 100) + '...' : result.persona}
                              </span>
                              <span className={`decision-badge ${result.decision.toLowerCase()}`}>
                                {result.decision === 'True' || result.decision === 'true' ? '찬성' : '반대'}
                              </span>
                            </div>
                            <p className="result-detailed" title={result.detailed}>
                              {result.detailed.length > 500 ? result.detailed.substring(0, 500) + '...' : result.detailed}
                            </p>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              );
              })
            )}
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

      <ConfirmDialog
        isOpen={showDeleteAllReferencesDialog}
        title="참고자료 전체 삭제 확인"
        message="모든 웹 검색 참고자료를 삭제하시겠습니까? 이 작업은 되돌릴 수 없습니다."
        confirmText="삭제"
        cancelText="취소"
        confirmButtonStyle="danger"
        onConfirm={confirmDeleteAllReferences}
        onCancel={() => setShowDeleteAllReferencesDialog(false)}
      />
    </div>
  );
}