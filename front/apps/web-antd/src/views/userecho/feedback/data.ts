import type { VbenFormSchema } from '#/adapter/form';
import type {
  OnActionClickFn,
  VxeGridProps,
} from '#/adapter/vxe-table';
import type { Feedback } from '#/api';

import { $t } from '@vben/locales';

import { z } from '#/adapter/form';

/** 查询表单配置 */
export const querySchema: VbenFormSchema[] = [
  {
    component: 'Input',
    fieldName: 'search_query',
    label: '内容搜索',
    componentProps: {
      placeholder: '搜索反馈内容或AI摘要（按 Enter 搜索）',
      allowClear: true,
    },
  },
  {
    component: 'RadioGroup',
    fieldName: 'search_mode',
    label: '搜索模式',
    defaultValue: 'keyword',
    componentProps: {
      options: [
        {
          label: '关键词 ⚡',
          value: 'keyword',
        },
        {
          label: '语义理解 🤖',
          value: 'semantic',
        },
      ],
      buttonStyle: 'solid',
      optionType: 'button',
      class: 'search-mode-radio',
    },
  },
  {
    component: 'Select',
    fieldName: 'is_urgent',
    label: '紧急程度',
    componentProps: {
      allowClear: true,
      options: [
        { label: '全部', value: '' },
        { label: '🔥 紧急', value: true },
        { label: '📝 常规', value: false },
      ],
    },
  },
  {
    component: 'Select',
    fieldName: 'has_topic',
    label: '是否已归类',
    componentProps: {
      allowClear: true,
      options: [
        { label: '全部', value: '' },
        { label: '已归类', value: true },
        { label: '未归类', value: false },
      ],
    },
  },
  {
    component: 'Select',
    fieldName: 'clustering_status',
    label: 'AI 状态',
    componentProps: {
      allowClear: true,
      options: [
        { label: '全部', value: '' },
        { label: '待处理', value: 'pending' },
        { label: '处理中', value: 'processing' },
        { label: '已处理', value: 'clustered' },
        { label: '失败', value: 'failed' },
      ],
    },
  },
];

/** 表格列配置 */
export function useColumns(
  onActionClick?: OnActionClickFn<Feedback>,
): VxeGridProps['columns'] {
  return [
    {
      field: 'seq',
      title: $t('common.table.id'),
      type: 'seq',
      fixed: 'left',
      width: 50,
    },
    {
      field: 'content',
      title: '反馈内容',
      minWidth: 300,
      showOverflow: 'tooltip',
    },
    {
      field: 'ai_summary',
      title: 'AI 摘要',
      width: 200,
      showOverflow: 'tooltip',
      formatter({ cellValue }) {
        return cellValue || '-';
      },
    },
    {
      field: 'images_metadata',
      title: '截图',
      width: 80,
      resizable: true,
      slots: { default: 'screenshots' },
    },
    {
      field: 'customer_name',
      title: '客户',
      width: 120,
      formatter({ row }) {
        return row.customer_name || '-';
      },
    },
    {
      field: 'topic_title',
      title: '所属主题',
      width: 150,
      slots: { default: 'topic' },
    },
    {
      field: 'clustering_status',
      title: 'AI 状态',
      width: 120,
      slots: { default: 'clustering_status' },
    },
    {
      field: 'is_urgent',
      title: '紧急程度',
      width: 100,
      slots: { default: 'urgent' },
    },
    {
      field: 'source',
      title: '来源',
      width: 100,
      formatter({ cellValue }) {
        const sourceMap: Record<string, string> = {
          manual: '手动录入',
          excel: 'Excel导入',
          api: 'API接入',
        };
        return sourceMap[cellValue] || cellValue;
      },
    },
    {
      field: 'submitted_at',
      title: '提交时间',
      width: 168,
      sortable: true,
    },
    {
      field: 'operation',
      title: $t('common.table.operation'),
      align: 'center',
      fixed: 'right',
      width: 150,
      cellRender: {
        attrs: {
          nameField: 'content',
          onClick: onActionClick,
        },
        name: 'CellOperation',
        options: [
          'edit',
          {
            code: 'delete',
            popconfirm: {
              title: '确认删除此反馈？',
            },
          },
        ],
      },
    },
  ];
}

/** 新建/编辑反馈表单 */
export const feedbackFormSchema: VbenFormSchema[] = [
  {
    component: 'Select',
    fieldName: 'board_id',
    label: '看板',
    rules: z.string().min(1, '请选择看板'),
    componentProps: {
      placeholder: '选择看板',
      allowClear: false,
      options: [], // 将在组件中动态加载
      style: { width: '100%' },
    },
  },
  {
    component: 'Textarea',
    fieldName: 'content',
    label: '反馈内容',
    rules: z.string().min(1, '请输入反馈内容').max(1000, '内容长度不能超过1000字'),
    componentProps: {
      rows: 8,
      placeholder: '请输入用户反馈内容...',
      showCount: true,
      maxlength: 1000,
      style: { width: '100%' },
    },
  },
  // customer_name 字段由 CustomerAutoComplete 组件单独处理
  {
    component: 'Switch',
    fieldName: 'is_urgent',
    label: '标记为紧急',
    defaultValue: false,
  },
];
