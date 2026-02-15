// 定价模块类型定义

export interface FeatureItem {
  text: string;
  included: boolean;
  highlight?: boolean;
}

export interface PricingTier {
  id: string;
  name: string;
  tagline: string;
  monthlyPrice: number;
  yearlyPrice: number;
  isRecommended: boolean;
  isFree: boolean;
  features: FeatureItem[];
  ctaText: string;
}

export type BillingPeriod = 'monthly' | 'yearly';

// 启航版功能列表
const getStarterFeatures = (): FeatureItem[] => [
  { text: '2,000条反馈/月', included: true },
  { text: '3个用户席位', included: true },
  { text: 'AI智能聚类（基础）', included: true },
  { text: '优先级评分（基础模型）', included: true },
  { text: '200次截图识别/月', included: true },
  { text: '语义搜索（基础）', included: true },
  { text: 'CSV + Excel数据导出', included: true },
  { text: '3个月历史数据保留', included: true },
  { text: '50个主题数量', included: true },
  { text: '基础团队协作', included: true },
  { text: '邮件技术支持', included: true },
  { text: 'API访问', included: false },
  { text: '私有部署', included: false },
];

// 中型版功能列表
const getStandardFeatures = (): FeatureItem[] => [
  { text: '10,000条反馈/月', included: true },
  { text: '10个用户席位', included: true },
  { text: 'AI智能聚类（高级）', included: true, highlight: true },
  { text: '优先级评分（标准模型）', included: true, highlight: true },
  { text: '1,000次截图识别/月', included: true },
  { text: '语义搜索（高级）', included: true, highlight: true },
  { text: 'CSV + Excel数据导出', included: true },
  { text: '1年历史数据保留', included: true },
  { text: '200个主题数量', included: true },
  { text: '团队权限管理', included: true, highlight: true },
  { text: '优先邮件支持', included: true },
  { text: '99.5% SLA保障', included: true },
  { text: '标准API访问', included: true, highlight: true },
  { text: '私有部署', included: false },
];

// 大型版功能列表
const getProFeatures = (): FeatureItem[] => [
  { text: '50,000条反馈/月', included: true },
  { text: '无限制用户席位', included: true, highlight: true },
  { text: 'AI智能聚类（高级+定制）', included: true, highlight: true },
  { text: '优先级评分（高级模型）', included: true, highlight: true },
  { text: '无限制截图识别', included: true },
  { text: '语义搜索（高级）', included: true, highlight: true },
  { text: '全格式导出 + API', included: true, highlight: true },
  { text: '永久历史数据保留', included: true },
  { text: '无限制主题数量', included: true },
  { text: '高级权限管理', included: true, highlight: true },
  { text: '专属客服支持', included: true, highlight: true },
  { text: '99.9% SLA保障', included: true },
  { text: '高级API访问', included: true, highlight: true },
  { text: '私有部署', included: false },
];

// 企业定制功能列表
const getEnterpriseFeatures = (): FeatureItem[] => [
  { text: '无限制反馈数量', included: true, highlight: true },
  { text: '无限制用户席位', included: true, highlight: true },
  { text: 'AI智能聚类（完全定制）', included: true, highlight: true },
  { text: '优先级评分（自定义模型）', included: true, highlight: true },
  { text: '无限制截图识别', included: true },
  { text: '语义搜索 + 企业知识库', included: true, highlight: true },
  { text: 'API优先访问', included: true, highlight: true },
  { text: '永久保留 + 数据归档', included: true },
  { text: '无限制主题数量', included: true },
  { text: 'SSO + 审计日志', included: true, highlight: true },
  { text: '1对1专属顾问', included: true, highlight: true },
  { text: '定制SLA保障', included: true },
  { text: '企业级API', included: true, highlight: true },
  { text: '私有化部署', included: true, highlight: true },
];

// 定价层级配置
export const pricingTiers: PricingTier[] = [
  {
    id: 'starter',
    name: '启航版',
    tagline: '适合个人产品经理与初创团队快速上手',
    monthlyPrice: 99,
    yearlyPrice: 799,
    isRecommended: false,
    isFree: false,
    features: getStarterFeatures(),
    ctaText: '立即订阅',
  },
  {
    id: 'standard',
    name: '专业版',
    tagline: '为成长型团队打造的全功能解决方案',
    monthlyPrice: 299,
    yearlyPrice: 2399,
    isRecommended: true,
    isFree: false,
    features: getStandardFeatures(),
    ctaText: '立即订阅',
  },
  {
    id: 'pro',
    name: '旗舰版',
    tagline: '赋能成熟企业与多产品线运营',
    monthlyPrice: 799,
    yearlyPrice: 6399,
    isRecommended: false,
    isFree: false,
    features: getProFeatures(),
    ctaText: '立即订阅',
  },
  {
    id: 'enterprise',
    name: '私有定制',
    tagline: '为大型企业量身定制的专属方案',
    monthlyPrice: 0,
    yearlyPrice: 0,
    isRecommended: false,
    isFree: false,
    features: getEnterpriseFeatures(),
    ctaText: '联系销售',
  },
];

// 计算年度节省金额
export const calculateSavings = (monthlyPrice: number): number => {
  const yearlyOriginal = monthlyPrice * 12;
  const yearlyPrice = Math.round(yearlyOriginal * 0.8); // 8折
  return yearlyOriginal - yearlyPrice;
};

// FAQ 数据
export interface FAQItem {
  question: string;
  answer: string;
}

export const faqItems: FAQItem[] = [
  {
    question: '可以随时升级或降级吗？',
    answer: '可以。您可以随时在账户设置中升级或降级套餐。升级后新配额立即生效，降级将在当前计费周期结束后生效。',
  },
  {
    question: '支持哪些支付方式？',
    answer: '我们支持支付宝、微信支付、银行卡等多种支付方式。企业客户还可以申请对公转账和发票开具服务。',
  },
  {
    question: '有免费试用期吗？',
    answer: '小型版永久免费，无需绑定信用卡。中型版和大型版提供7天免费试用，试用期结束前可随时取消，不会产生费用。',
  },
  {
    question: '超出配额怎么办？',
    answer: '当反馈数量超出套餐配额时，您可以购买额外的反馈包（¥99/1000条），或者升级到更高套餐。我们会提前通知您配额使用情况。',
  },
  {
    question: '数据安全有保障吗？',
    answer: '我们采用银行级加密技术，所有数据传输使用SSL加密，数据存储采用多重备份。企业版支持私有化部署，数据完全自主可控。',
  },
  {
    question: '可以取消订阅吗？',
    answer: '可以随时取消订阅，取消后当前计费周期内仍可继续使用服务，周期结束后自动降级为免费版。',
  },
];
