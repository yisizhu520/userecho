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
      field: 'customer_name',
      title: '客户',
      width: 120,
      formatter({ row }) {
        return row.customer_name || row.anonymous_author || '-';
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
    label: 'Board',
    rules: z.string().min(1, '请选择 Board'),
    componentProps: {
      placeholder: '选择 Board',
      allowClear: false,
      options: [], // 将在组件中动态加载
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
    },
  },
  {
    component: 'Input',
    fieldName: 'customer_name',
    label: '客户名称',
    rules: z.string().optional().refine((val, ctx) => {
      const anonymousAuthor = ctx.parent.anonymous_author;
      return val || anonymousAuthor;
    }, '客户名称和匿名作者至少填写一个'),
    componentProps: {
      placeholder: '输入客户名称',
    },
  },
  {
    component: 'Input',
    fieldName: 'anonymous_author',
    label: '匿名作者',
    rules: z.string().optional().refine((val, ctx) => {
      const customerName = ctx.parent.customer_name;
      return val || customerName;
    }, '客户名称和匿名作者至少填写一个'),
    componentProps: {
      placeholder: '如：小红书用户@xxx',
    },
  },
  {
    component: 'Input',
    fieldName: 'anonymous_source',
    label: '来源平台',
    componentProps: {
      placeholder: '如：微信、小红书、知乎等',
    },
  },
  {
    component: 'Switch',
    fieldName: 'is_urgent',
    label: '标记为紧急',
    defaultValue: false,
  },
];
