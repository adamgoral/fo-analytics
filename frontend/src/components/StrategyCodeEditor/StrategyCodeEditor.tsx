import React, { useRef, useState } from 'react';
import Editor, { Monaco } from '@monaco-editor/react';
import { editor } from 'monaco-editor';
import { Box, Paper, Typography, IconButton, Select, MenuItem, FormControl, InputLabel, Stack } from '@mui/material';
import { Save as SaveIcon, PlayArrow as RunIcon, ContentCopy as CopyIcon } from '@mui/icons-material';

interface StrategyCodeEditorProps {
  code: string;
  language?: string;
  onChange?: (value: string | undefined) => void;
  onSave?: (code: string) => void;
  onRun?: (code: string) => void;
  readOnly?: boolean;
  height?: string;
  title?: string;
}

const SUPPORTED_LANGUAGES = [
  { value: 'python', label: 'Python' },
  { value: 'javascript', label: 'JavaScript' },
  { value: 'typescript', label: 'TypeScript' },
];

const EDITOR_OPTIONS: editor.IStandaloneEditorConstructionOptions = {
  fontSize: 14,
  minimap: { enabled: false },
  scrollbar: {
    vertical: 'visible',
    horizontal: 'visible',
  },
  lineNumbers: 'on',
  glyphMargin: true,
  folding: true,
  lineDecorationsWidth: 10,
  lineNumbersMinChars: 3,
  renderLineHighlight: 'all',
  scrollBeyondLastLine: false,
  automaticLayout: true,
  tabSize: 4,
  insertSpaces: true,
  wordWrap: 'on',
  wrappingStrategy: 'advanced',
  suggest: {
    showMethods: true,
    showFunctions: true,
    showConstructors: true,
    showFields: true,
    showVariables: true,
    showClasses: true,
    showStructs: true,
    showInterfaces: true,
    showModules: true,
    showProperties: true,
    showEvents: true,
    showOperators: true,
    showUnits: true,
    showValues: true,
    showConstants: true,
    showEnums: true,
    showEnumMembers: true,
    showKeywords: true,
    showWords: true,
    showColors: true,
    showFiles: true,
    showReferences: true,
    showFolders: true,
    showTypeParameters: true,
    showSnippets: true,
  },
};

export const StrategyCodeEditor: React.FC<StrategyCodeEditorProps> = ({
  code,
  language = 'python',
  onChange,
  onSave,
  onRun,
  readOnly = false,
  height = '600px',
  title = 'Strategy Code',
}) => {
  const editorRef = useRef<editor.IStandaloneCodeEditor | null>(null);
  const [selectedLanguage, setSelectedLanguage] = useState(language);

  const handleEditorDidMount = (editor: editor.IStandaloneCodeEditor, monaco: Monaco) => {
    editorRef.current = editor;

    // Configure Python language settings
    if (selectedLanguage === 'python') {
      monaco.languages.setLanguageConfiguration('python', {
        indentationRules: {
          increaseIndentPattern: /^.*:\s*$/,
          decreaseIndentPattern: /^\s*(elif|else|except|finally).*:/,
        },
      });

      // Add Python-specific snippets
      monaco.languages.registerCompletionItemProvider('python', {
        provideCompletionItems: (model, position) => {
          const suggestions = [
            {
              label: 'strategy_function',
              kind: monaco.languages.CompletionItemKind.Snippet,
              insertText: [
                'def calculate_signals(data: pd.DataFrame) -> pd.Series:',
                '    """',
                '    Calculate trading signals based on the strategy logic.',
                '    ',
                '    Args:',
                '        data: DataFrame with OHLCV data',
                '    ',
                '    Returns:',
                '        Series with signals: 1 (buy), -1 (sell), 0 (hold)',
                '    """',
                '    signals = pd.Series(0, index=data.index)',
                '    ',
                '    # Add your strategy logic here',
                '    ${1:# Example: Simple moving average crossover}',
                '    ',
                '    return signals',
              ].join('\n'),
              insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
              documentation: 'Create a strategy function template',
            },
            {
              label: 'import_common',
              kind: monaco.languages.CompletionItemKind.Snippet,
              insertText: [
                'import pandas as pd',
                'import numpy as np',
                'from typing import Dict, List, Optional',
                'import talib',
              ].join('\n'),
              documentation: 'Import common libraries for strategy development',
            },
          ];

          return { suggestions };
        },
      });
    }

    // Configure theme
    monaco.editor.defineTheme('strategyTheme', {
      base: 'vs-dark',
      inherit: true,
      rules: [
        { token: 'comment', foreground: '6A9955' },
        { token: 'keyword', foreground: '569CD6' },
        { token: 'string', foreground: 'CE9178' },
      ],
      colors: {
        'editor.background': '#1E1E1E',
        'editor.foreground': '#D4D4D4',
        'editor.lineHighlightBackground': '#2A2A2A',
        'editorLineNumber.foreground': '#858585',
        'editor.selectionBackground': '#264F78',
        'editor.inactiveSelectionBackground': '#3A3D41',
      },
    });
    monaco.editor.setTheme('strategyTheme');
  };

  const handleCopy = () => {
    if (editorRef.current) {
      const code = editorRef.current.getValue();
      navigator.clipboard.writeText(code);
    }
  };

  const handleSave = () => {
    if (editorRef.current && onSave) {
      const code = editorRef.current.getValue();
      onSave(code);
    }
  };

  const handleRun = () => {
    if (editorRef.current && onRun) {
      const code = editorRef.current.getValue();
      onRun(code);
    }
  };

  const handleLanguageChange = (event: any) => {
    setSelectedLanguage(event.target.value);
  };

  return (
    <Paper elevation={2} sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <Box sx={{ p: 2, borderBottom: 1, borderColor: 'divider' }}>
        <Stack direction="row" justifyContent="space-between" alignItems="center">
          <Typography variant="h6">{title}</Typography>
          <Stack direction="row" spacing={2} alignItems="center">
            <FormControl size="small" sx={{ minWidth: 120 }}>
              <InputLabel>Language</InputLabel>
              <Select
                value={selectedLanguage}
                onChange={handleLanguageChange}
                label="Language"
                disabled={readOnly}
              >
                {SUPPORTED_LANGUAGES.map((lang) => (
                  <MenuItem key={lang.value} value={lang.value}>
                    {lang.label}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
            <IconButton onClick={handleCopy} title="Copy code">
              <CopyIcon />
            </IconButton>
            {onRun && !readOnly && (
              <IconButton onClick={handleRun} color="primary" title="Run strategy">
                <RunIcon />
              </IconButton>
            )}
            {onSave && !readOnly && (
              <IconButton onClick={handleSave} color="primary" title="Save strategy">
                <SaveIcon />
              </IconButton>
            )}
          </Stack>
        </Stack>
      </Box>
      <Box sx={{ flexGrow: 1, overflow: 'hidden' }}>
        <Editor
          height={height}
          language={selectedLanguage}
          value={code}
          onChange={onChange}
          onMount={handleEditorDidMount}
          options={{
            ...EDITOR_OPTIONS,
            readOnly,
          }}
          theme="strategyTheme"
        />
      </Box>
    </Paper>
  );
};

export default StrategyCodeEditor;