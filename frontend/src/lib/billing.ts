import { useSubscriptionStore, SubscriptionTier } from '../stores/subscriptionStore';

const GOOGLE_PLAY_PRODUCTS = {
  pro_monthly: 'com.mumap.agents.pro.monthly',
  pro_yearly: 'com.mumap.agents.pro.yearly',
  team_monthly: 'com.mumap.agents.team.monthly',
  team_yearly: 'com.mumap.agents.team.yearly',
};

export async function initializeBilling(): Promise<boolean> {
  try {
    const { Capacitor } = await import('@capacitor/core');
    if (Capacitor.getPlatform() !== 'android') return true;

    const { NativePurchases, PURCHASE_TYPE } = await import('@capgo/native-purchases');
    const { isBillingSupported } = await NativePurchases.isBillingSupported();
    return isBillingSupported;
  } catch {
    return false;
  }
}

export async function getSubscriptionProducts() {
  try {
    const { Capacitor } = await import('@capacitor/core');
    if (Capacitor.getPlatform() !== 'android') return [];

    const { NativePurchases, PURCHASE_TYPE } = await import('@capgo/native-purchases');
    const { products } = await NativePurchases.getProducts({
      productIdentifiers: Object.values(GOOGLE_PLAY_PRODUCTS),
      productType: PURCHASE_TYPE.SUBS,
    });
    return products;
  } catch {
    return [];
  }
}

export async function purchaseSubscription(
  tier: SubscriptionTier,
  period: 'monthly' | 'yearly' = 'monthly'
): Promise<boolean> {
  const productId =
    tier === 'pro'
      ? period === 'monthly'
        ? GOOGLE_PLAY_PRODUCTS.pro_monthly
        : GOOGLE_PLAY_PRODUCTS.pro_yearly
      : period === 'monthly'
        ? GOOGLE_PLAY_PRODUCTS.team_monthly
        : GOOGLE_PLAY_PRODUCTS.team_yearly;

  try {
    const { Capacitor } = await import('@capacitor/core');
    if (Capacitor.getPlatform() !== 'android') {
      useSubscriptionStore.getState().setTier(tier, 'web-subscription');
      return true;
    }

    const { NativePurchases, PURCHASE_TYPE } = await import('@capgo/native-purchases');
    const planId = period === 'monthly' ? `${tier}-monthly` : `${tier}-yearly`;

    const transaction = await NativePurchases.purchaseProduct({
      productIdentifier: productId,
      planIdentifier: planId,
      productType: PURCHASE_TYPE.SUBS,
    });

    if (transaction) {
      useSubscriptionStore.getState().setTier(tier, transaction.purchaseToken || transaction.transactionId || productId);
      return true;
    }
    return false;
  } catch (error: any) {
    if (error?.code === 'USER_CANCELLED') return false;
    console.error('Purchase failed:', error);
    return false;
  }
}

export async function restorePurchases(): Promise<boolean> {
  try {
    const { Capacitor } = await import('@capacitor/core');
    if (Capacitor.getPlatform() !== 'android') return false;

    const { NativePurchases, PURCHASE_TYPE } = await import('@capgo/native-purchases');
    await NativePurchases.restorePurchases();

    const { purchases } = await NativePurchases.getPurchases({
      productType: PURCHASE_TYPE.SUBS,
    });

    const active = purchases.find(
      (p: any) => p.purchaseState === 'PURCHASED' || p.purchaseState === '1'
    );

    if (active) {
      const tier: SubscriptionTier = active.productIdentifier.includes('team') ? 'team' : 'pro';
      useSubscriptionStore.getState().setTier(tier, active.purchaseToken || active.productIdentifier);
      return true;
    }
    return false;
  } catch {
    return false;
  }
}

export function isFeatureGated(feature: string): boolean {
  const store = useSubscriptionStore.getState();
  switch (feature) {
    case 'templates':
      return !store.hasTemplatesAccess();
    case 'analytics':
      return !store.hasAnalytics();
    case 'api':
      return !store.hasApiAccess();
    case 'team':
      return !store.hasTeamFeatures();
    case 'agent':
      return !store.canCreateAgent(0);
    default:
      return false;
  }
}
