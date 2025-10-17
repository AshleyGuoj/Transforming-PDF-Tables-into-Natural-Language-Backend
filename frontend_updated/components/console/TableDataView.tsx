'use client';

import { useState, useEffect } from 'react';
import API from '../../lib/api';

interface TableData {
  table_id: number;
  file_id: number;
  page_number: number;
  bbox: {
    x: number;
    y: number;
    width: number;
    height: number;
  };
  headers: string[][];
  rows: string[][];
  confidence: number | null;
  table_json: any;
}

interface FileData {
  file_id: number;
  project_id: number;
  file_name: string;
  file_size: number;
  mime_type: string;
  created_at: string;
  updated_at: string;
}

interface ProjectData {
  project_id: number;
  org_id: number;
  name: string;
  description: string;
  status: string;
}

export default function TableDataView() {
  const [tables, setTables] = useState<TableData[]>([]);
  const [files, setFiles] = useState<FileData[]>([]);
  const [projects, setProjects] = useState<ProjectData[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedFile, setSelectedFile] = useState<number | null>(null);
  const [showTableModal, setShowTableModal] = useState(false);
  const [selectedTable, setSelectedTable] = useState<TableData | null>(null);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);

      // 加载项目数据
      const projectsData = await API.projects.getAll();
      setProjects(Array.isArray(projectsData) ? projectsData : []);

      // 加载第一个项目的文件数据
      if (Array.isArray(projectsData) && projectsData.length > 0) {
        const firstProject = projectsData[0];
        const filesData = await API.files.getByProject(firstProject.project_id);
        setFiles(filesData.files || []);

        // 加载所有文件的表格数据
        if (filesData.files && filesData.files.length > 0) {
          const allTables: TableData[] = [];
          for (const file of filesData.files) {
            try {
              const tablesData = await API.parse.getTables(file.file_id);
              if (tablesData.tables) {
                allTables.push(...tablesData.tables);
              }
            } catch (err) {
              console.warn(`Failed to load tables for file ${file.file_id}:`, err);
            }
          }
          setTables(allTables);
        }
      }
    } catch (err) {
      console.error('Failed to load data:', err);
      setError('Failed to load table data');
    } finally {
      setLoading(false);
    }
  };

  const getFileInfo = (fileId: number) => {
    return files.find(f => f.file_id === fileId);
  };

  const getProjectInfo = (projectId: number) => {
    return projects.find(p => p.project_id === projectId);
  };

  const handleViewTable = (table: TableData) => {
    setSelectedTable(table);
    setShowTableModal(true);
  };

  const renderTable = (table: TableData) => {
    if (!table.headers || !table.rows) {
      return <div className="text-gray-500 text-sm">No table data available</div>;
    }

    return (
      <div className="overflow-x-auto">
        <table className="min-w-full border-collapse border border-gray-300">
          <thead>
            <tr>
              {table.headers[0].map((header, index) => (
                <th
                  key={index}
                  className="border border-gray-300 px-3 py-2 bg-gray-50 text-left text-xs font-medium text-gray-700 uppercase tracking-wider"
                >
                  {header || `Column ${index + 1}`}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {table.rows.slice(0, 10).map((row, rowIndex) => (
              <tr key={rowIndex} className={rowIndex % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                {row.map((cell, cellIndex) => (
                  <td
                    key={cellIndex}
                    className="border border-gray-300 px-3 py-2 text-sm text-gray-900"
                  >
                    {cell || '-'}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
        {table.rows.length > 10 && (
          <div className="text-xs text-gray-500 mt-2">
            Showing first 10 rows of {table.rows.length} total rows
          </div>
        )}
      </div>
    );
  };

  if (loading) {
    return (
      <div className="p-6">
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          <span className="ml-2 text-gray-600">Loading table data...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex">
            <i className="ri-error-warning-line w-5 h-5 text-red-400"></i>
            <div className="ml-3">
              <h3 className="text-sm font-medium text-red-800">Error loading data</h3>
              <p className="mt-1 text-sm text-red-700">{error}</p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold text-gray-900">Extracted Tables</h2>
          <p className="text-sm text-gray-600 mt-1">
            View and manage tables extracted from PDF files
          </p>
        </div>
        <div className="flex items-center space-x-3">
          <span className="text-sm text-gray-500">
            {tables.length} tables found
          </span>
          <button
            onClick={loadData}
            className="px-3 py-2 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center space-x-2"
          >
            <i className="ri-refresh-line w-4 h-4"></i>
            <span>Refresh</span>
          </button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <div className="flex items-center">
            <div className="p-2 bg-blue-100 rounded-lg">
              <i className="ri-table-line w-6 h-6 text-blue-600"></i>
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Total Tables</p>
              <p className="text-2xl font-semibold text-gray-900">{tables.length}</p>
            </div>
          </div>
        </div>
        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <div className="flex items-center">
            <div className="p-2 bg-green-100 rounded-lg">
              <i className="ri-file-line w-6 h-6 text-green-600"></i>
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Files Processed</p>
              <p className="text-2xl font-semibold text-gray-900">{files.length}</p>
            </div>
          </div>
        </div>
        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <div className="flex items-center">
            <div className="p-2 bg-purple-100 rounded-lg">
              <i className="ri-folder-line w-6 h-6 text-purple-600"></i>
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Projects</p>
              <p className="text-2xl font-semibold text-gray-900">{projects.length}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Tables List */}
      <div className="bg-white rounded-lg border border-gray-200">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-medium text-gray-900">Table List</h3>
        </div>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Table Info
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  File/Project
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Table Structure
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Page
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {tables.map((table) => {
                const file = getFileInfo(table.file_id);
                const project = file ? getProjectInfo(file.project_id) : null;
                
                return (
                  <tr key={table.table_id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                          <span className="text-sm font-medium text-blue-600">
                            T{table.table_id}
                          </span>
                        </div>
                        <div className="ml-3">
                          <div className="text-sm font-medium text-gray-900">
                            Table {table.table_id}
                          </div>
                          <div className="text-sm text-gray-500">
                            ID: {table.table_id}
                          </div>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-900">
                        {file?.file_name || 'Unknown File'}
                      </div>
                      <div className="text-sm text-gray-500">
                        {project?.name || 'Unknown Project'}
                      </div>
                      <div className="text-xs text-gray-400">
                        {file ? `${(file.file_size / 1024).toFixed(1)} KB` : ''}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-900">
                        {table.headers?.[0]?.length || 0} × {table.rows?.length || 0}
                      </div>
                      <div className="text-sm text-gray-500">
                        {table.headers?.[0]?.length || 0} columns, {table.rows?.length || 0} rows
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                        Page {table.page_number}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                      <button
                        onClick={() => handleViewTable(table)}
                        className="text-blue-600 hover:text-blue-900 mr-3"
                      >
                        View Details
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Table Detail Modal */}
      {showTableModal && selectedTable && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-11/12 max-w-6xl shadow-lg rounded-md bg-white">
            <div className="mt-3">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-medium text-gray-900">
                  Table {selectedTable.table_id} Details
                </h3>
                <button
                  onClick={() => setShowTableModal(false)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <i className="ri-close-line w-6 h-6"></i>
                </button>
              </div>
              
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="font-medium text-gray-700">Table ID:</span>
                    <span className="ml-2 text-gray-900">{selectedTable.table_id}</span>
                  </div>
                  <div>
                    <span className="font-medium text-gray-700">Page:</span>
                    <span className="ml-2 text-gray-900">{selectedTable.page_number}</span>
                  </div>
                  <div>
                    <span className="font-medium text-gray-700">Dimensions:</span>
                    <span className="ml-2 text-gray-900">
                      {selectedTable.headers?.[0]?.length || 0} × {selectedTable.rows?.length || 0}
                    </span>
                  </div>
                  <div>
                    <span className="font-medium text-gray-700">Confidence:</span>
                    <span className="ml-2 text-gray-900">
                      {selectedTable.confidence ? `${(selectedTable.confidence * 100).toFixed(1)}%` : 'N/A'}
                    </span>
                  </div>
                </div>
                
                <div className="border-t pt-4">
                  <h4 className="text-md font-medium text-gray-900 mb-3">Table Content</h4>
                  {renderTable(selectedTable)}
                </div>
              </div>
              
              <div className="flex justify-end mt-6">
                <button
                  onClick={() => setShowTableModal(false)}
                  className="px-4 py-2 bg-gray-300 text-gray-700 rounded-lg hover:bg-gray-400"
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
