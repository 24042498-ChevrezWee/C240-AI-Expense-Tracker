import { getDashboardData, getFriendlyErrorMessage, getUserReceipts } from "./apiService";

const emptySummary = {
    totalExpenses: 0,
    receiptCount: 0,
    monthlySpending: 0,
    topCategory: "-",
    largestExpense: "-",
    averageExpense: 0,
    categories: [],
    recentReceipts: [],
};

export async function getDashboardSummary(userId) {
    try {
        if (!userId) {
            return emptySummary;
        }

        const data = await getDashboardData(userId);
        return {
            ...emptySummary,
            ...data,
        };
    } catch (error) {
        throw new Error(getFriendlyErrorMessage(error, "We’re having trouble loading your dashboard right now. Please try again in a moment."));
    }
}

export async function getRecentReceipts(userId) {
    try {
        if (!userId) {
            return [];
        }

        return await getUserReceipts(userId);
    } catch (error) {
        throw new Error(getFriendlyErrorMessage(error, "We’re having trouble loading your recent receipts right now."));
    }
}

export function saveRecentReceipt(receipt) {
    if (!receipt?.id) {
        return [];
    }

    const existing = [];
    const next = [receipt, ...existing.filter((item) => item.id !== receipt.id)].slice(0, 8);
    return next;
}