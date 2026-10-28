export type Json = string | number | boolean | null | { [key: string]: Json | undefined } | Json[];

export type Database = {
  public: {
    Tables: {
      stock: {
        Row: {
          address: string | null;
          city: string | null;
          country: string | null;
          currency: string | null;
          description: string | null;
          employees: number | null;
          exchange: string | null;
          id: number;
          industry: string | null;
          key_executives: Json | null;
          logo: string | null;
          maintenance_update: string | null;
          name: string;
          phone_number: string | null;
          sector: string | null;
          symbol: string;
          website: string | null;
          zip: string | null;
        };
        ComputedFields: never;
        Insert: {
          address?: string | null;
          city?: string | null;
          country?: string | null;
          currency?: string | null;
          description?: string | null;
          employees?: number | null;
          exchange?: string | null;
          id?: number;
          industry?: string | null;
          key_executives?: Json | null;
          logo?: string | null;
          maintenance_update?: string | null;
          name: string;
          phone_number?: string | null;
          sector?: string | null;
          symbol: string;
          website?: string | null;
          zip?: string | null;
        };
        Update: {
          address?: string | null;
          city?: string | null;
          country?: string | null;
          currency?: string | null;
          description?: string | null;
          employees?: number | null;
          exchange?: string | null;
          id?: number;
          industry?: string | null;
          key_executives?: Json | null;
          logo?: string | null;
          maintenance_update?: string | null;
          name?: string;
          phone_number?: string | null;
          sector?: string | null;
          symbol?: string;
          website?: string | null;
          zip?: string | null;
        };
        Relationships: [];
      };
      stock_balance_sheet: {
        Row: {
          cash_cash_equivalents_and_short_term_investments: number | null;
          current_assets: number | null;
          current_liabilities: number | null;
          fiscal_date: string;
          net_tangible_assets: number | null;
          period: Database["public"]["Enums"]["statement_period"];
          retained_earnings: number | null;
          share_issued: number | null;
          stock_id: number;
          stockholders_equity: number | null;
          total_assets: number | null;
          total_debt: number | null;
          total_liabilities_net_minority_interest: number | null;
        };
        ComputedFields: never;
        Insert: {
          cash_cash_equivalents_and_short_term_investments?: number | null;
          current_assets?: number | null;
          current_liabilities?: number | null;
          fiscal_date: string;
          net_tangible_assets?: number | null;
          period: Database["public"]["Enums"]["statement_period"];
          retained_earnings?: number | null;
          share_issued?: number | null;
          stock_id: number;
          stockholders_equity?: number | null;
          total_assets?: number | null;
          total_debt?: number | null;
          total_liabilities_net_minority_interest?: number | null;
        };
        Update: {
          cash_cash_equivalents_and_short_term_investments?: number | null;
          current_assets?: number | null;
          current_liabilities?: number | null;
          fiscal_date?: string;
          net_tangible_assets?: number | null;
          period?: Database["public"]["Enums"]["statement_period"];
          retained_earnings?: number | null;
          share_issued?: number | null;
          stock_id?: number;
          stockholders_equity?: number | null;
          total_assets?: number | null;
          total_debt?: number | null;
          total_liabilities_net_minority_interest?: number | null;
        };
        Relationships: [
          {
            foreignKeyName: "stocks_balance_sheets_stock_id_fkey";
            columns: ["stock_id"];
            isOneToOne: false;
            referencedRelation: "stock";
            referencedColumns: ["id"];
          },
        ];
      };
      stock_cash_flow: {
        Row: {
          capital_expenditure: number | null;
          fiscal_date: string;
          free_cash_flow: number | null;
          operating_cash_flow: number | null;
          period: Database["public"]["Enums"]["statement_period"];
          stock_id: number;
        };
        ComputedFields: never;
        Insert: {
          capital_expenditure?: number | null;
          fiscal_date: string;
          free_cash_flow?: number | null;
          operating_cash_flow?: number | null;
          period: Database["public"]["Enums"]["statement_period"];
          stock_id: number;
        };
        Update: {
          capital_expenditure?: number | null;
          fiscal_date?: string;
          free_cash_flow?: number | null;
          operating_cash_flow?: number | null;
          period?: Database["public"]["Enums"]["statement_period"];
          stock_id?: number;
        };
        Relationships: [
          {
            foreignKeyName: "stocks_cash_flows_stock_id_fkey";
            columns: ["stock_id"];
            isOneToOne: false;
            referencedRelation: "stock";
            referencedColumns: ["id"];
          },
        ];
      };
      stock_dividend: {
        Row: {
          date: string;
          dividend: number;
          stock_id: number;
        };
        ComputedFields: never;
        Insert: {
          date: string;
          dividend: number;
          stock_id: number;
        };
        Update: {
          date?: string;
          dividend?: number;
          stock_id?: number;
        };
        Relationships: [
          {
            foreignKeyName: "stocks_dividends_stock_id_fkey";
            columns: ["stock_id"];
            isOneToOne: false;
            referencedRelation: "stock";
            referencedColumns: ["id"];
          },
        ];
      };
      stock_financial_analysis: {
        Row: {
          assets_price: number | null;
          capital_index: number | null;
          current_ratio: number | null;
          debt_growth: number | null;
          debt_to_equity: number | null;
          dividend_yield: number | null;
          earning_per_share: number | null;
          fiscal_date: string;
          gross_income_growth: number | null;
          gross_margin: number | null;
          maintenance_update: string;
          median_comparison: number | null;
          net_income_growth: number | null;
          net_margin: number | null;
          operating_margin: number | null;
          payback_period: number | null;
          pb_ratio: number | null;
          pe_ratio: number | null;
          period: Database["public"]["Enums"]["statement_period"];
          quality_score: number | null;
          retained_earning_growth: number | null;
          return_on_equity: number | null;
          revenue_growth: number | null;
          revenues_per_share: number | null;
          stock_id: number;
        };
        ComputedFields: never;
        Insert: {
          assets_price?: number | null;
          capital_index?: number | null;
          current_ratio?: number | null;
          debt_growth?: number | null;
          debt_to_equity?: number | null;
          dividend_yield?: number | null;
          earning_per_share?: number | null;
          fiscal_date: string;
          gross_income_growth?: number | null;
          gross_margin?: number | null;
          maintenance_update: string;
          median_comparison?: number | null;
          net_income_growth?: number | null;
          net_margin?: number | null;
          operating_margin?: number | null;
          payback_period?: number | null;
          pb_ratio?: number | null;
          pe_ratio?: number | null;
          period: Database["public"]["Enums"]["statement_period"];
          quality_score?: number | null;
          retained_earning_growth?: number | null;
          return_on_equity?: number | null;
          revenue_growth?: number | null;
          revenues_per_share?: number | null;
          stock_id: number;
        };
        Update: {
          assets_price?: number | null;
          capital_index?: number | null;
          current_ratio?: number | null;
          debt_growth?: number | null;
          debt_to_equity?: number | null;
          dividend_yield?: number | null;
          earning_per_share?: number | null;
          fiscal_date?: string;
          gross_income_growth?: number | null;
          gross_margin?: number | null;
          maintenance_update?: string;
          median_comparison?: number | null;
          net_income_growth?: number | null;
          net_margin?: number | null;
          operating_margin?: number | null;
          payback_period?: number | null;
          pb_ratio?: number | null;
          pe_ratio?: number | null;
          period?: Database["public"]["Enums"]["statement_period"];
          quality_score?: number | null;
          retained_earning_growth?: number | null;
          return_on_equity?: number | null;
          revenue_growth?: number | null;
          revenues_per_share?: number | null;
          stock_id?: number;
        };
        Relationships: [
          {
            foreignKeyName: "stock_financial_analysis_stock_id_fkey";
            columns: ["stock_id"];
            isOneToOne: false;
            referencedRelation: "stock";
            referencedColumns: ["id"];
          },
        ];
      };
      stock_historical_price: {
        Row: {
          adj_close: number | null;
          close: number;
          date: string;
          high: number | null;
          low: number | null;
          open: number;
          stock_id: number;
          volume: number | null;
        };
        ComputedFields: never;
        Insert: {
          adj_close?: number | null;
          close: number;
          date: string;
          high?: number | null;
          low?: number | null;
          open: number;
          stock_id: number;
          volume?: number | null;
        };
        Update: {
          adj_close?: number | null;
          close?: number;
          date?: string;
          high?: number | null;
          low?: number | null;
          open?: number;
          stock_id?: number;
          volume?: number | null;
        };
        Relationships: [
          {
            foreignKeyName: "stocks_historical_prices_stock_id_fkey";
            columns: ["stock_id"];
            isOneToOne: false;
            referencedRelation: "stock";
            referencedColumns: ["id"];
          },
        ];
      };
      stock_income_statement: {
        Row: {
          basic_average_shares: number | null;
          fiscal_date: string;
          gross_profit: number | null;
          net_income: number | null;
          operating_income: number | null;
          otherunder_preferred_stock_dividend: number | null;
          period: Database["public"]["Enums"]["statement_period"];
          stock_id: number;
          total_revenue: number | null;
        };
        ComputedFields: never;
        Insert: {
          basic_average_shares?: number | null;
          fiscal_date: string;
          gross_profit?: number | null;
          net_income?: number | null;
          operating_income?: number | null;
          otherunder_preferred_stock_dividend?: number | null;
          period: Database["public"]["Enums"]["statement_period"];
          stock_id: number;
          total_revenue?: number | null;
        };
        Update: {
          basic_average_shares?: number | null;
          fiscal_date?: string;
          gross_profit?: number | null;
          net_income?: number | null;
          operating_income?: number | null;
          otherunder_preferred_stock_dividend?: number | null;
          period?: Database["public"]["Enums"]["statement_period"];
          stock_id?: number;
          total_revenue?: number | null;
        };
        Relationships: [
          {
            foreignKeyName: "stocks_income_statements_stock_id_fkey";
            columns: ["stock_id"];
            isOneToOne: false;
            referencedRelation: "stock";
            referencedColumns: ["id"];
          },
        ];
      };
      stock_metric: {
        Row: {
          currency: string | null;
          maintenance_update: string;
          market_cap: number | null;
          regular_market_change: number | null;
          regular_market_change_percent: number | null;
          regular_market_time: string | null;
          stock_id: number;
          stock_price: number | null;
        };
        ComputedFields: never;
        Insert: {
          currency?: string | null;
          maintenance_update: string;
          market_cap?: number | null;
          regular_market_change?: number | null;
          regular_market_change_percent?: number | null;
          regular_market_time?: string | null;
          stock_id: number;
          stock_price?: number | null;
        };
        Update: {
          currency?: string | null;
          maintenance_update?: string;
          market_cap?: number | null;
          regular_market_change?: number | null;
          regular_market_change_percent?: number | null;
          regular_market_time?: string | null;
          stock_id?: number;
          stock_price?: number | null;
        };
        Relationships: [
          {
            foreignKeyName: "stocks_statistics_stock_id_fkey";
            columns: ["stock_id"];
            isOneToOne: true;
            referencedRelation: "stock";
            referencedColumns: ["id"];
          },
        ];
      };
      stock_split: {
        Row: {
          date: string;
          factor: number;
          stock_id: number;
        };
        ComputedFields: never;
        Insert: {
          date: string;
          factor: number;
          stock_id: number;
        };
        Update: {
          date?: string;
          factor?: number;
          stock_id?: number;
        };
        Relationships: [
          {
            foreignKeyName: "stocks_stock_splits_stock_id_fkey";
            columns: ["stock_id"];
            isOneToOne: false;
            referencedRelation: "stock";
            referencedColumns: ["id"];
          },
        ];
      };
      symbol_activity: {
        Row: {
          last_visit: string;
          symbol: string;
        };
        ComputedFields: never;
        Insert: {
          last_visit?: string;
          symbol: string;
        };
        Update: {
          last_visit?: string;
          symbol?: string;
        };
        Relationships: [];
      };
      watchlist: {
        Row: {
          created_at: string;
          id: number;
          name: string;
          user_id: string;
        };
        ComputedFields: never;
        Insert: {
          created_at?: string;
          id?: number;
          name: string;
          user_id?: string;
        };
        Update: {
          created_at?: string;
          id?: number;
          name?: string;
          user_id?: string;
        };
        Relationships: [];
      };
      watchlist_item: {
        Row: {
          added_at: string;
          stock_id: number;
          watchlist_id: number;
        };
        ComputedFields: never;
        Insert: {
          added_at?: string;
          stock_id: number;
          watchlist_id: number;
        };
        Update: {
          added_at?: string;
          stock_id?: number;
          watchlist_id?: number;
        };
        Relationships: [
          {
            foreignKeyName: "watchlist_item_stock_id_fkey";
            columns: ["stock_id"];
            isOneToOne: false;
            referencedRelation: "stock";
            referencedColumns: ["id"];
          },
          {
            foreignKeyName: "watchlist_item_watchlist_id_fkey";
            columns: ["watchlist_id"];
            isOneToOne: false;
            referencedRelation: "watchlist";
            referencedColumns: ["id"];
          },
        ];
      };
    };
    Views: {
      [_ in never]: never;
    };
    Functions: {
      get_all_medians: { Args: Record<PropertyKey, never>; Returns: Json };
    };
    Enums: {
      statement_period: "Q1" | "Q2" | "Q3" | "Q4" | "FY" | "TTM";
    };
    CompositeTypes: {
      [_ in never]: never;
    };
  };
};

type DatabaseWithoutInternals = Omit<Database, "__InternalSupabase">;

type DefaultSchema = DatabaseWithoutInternals[Extract<keyof Database, "public">];

export type Tables<
  DefaultSchemaTableNameOrOptions extends
    | keyof (DefaultSchema["Tables"] & DefaultSchema["Views"])
    | { schema: keyof DatabaseWithoutInternals },
  TableName extends (DefaultSchemaTableNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals;
  }
    ? keyof (DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"] &
        DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Views"])
    : never) = never,
> = DefaultSchemaTableNameOrOptions extends { schema: keyof DatabaseWithoutInternals }
  ? (DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"] &
      DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Views"])[TableName] extends {
      Row: infer R;
    }
    ? R
    : never
  : DefaultSchemaTableNameOrOptions extends keyof (DefaultSchema["Tables"] & DefaultSchema["Views"])
    ? (DefaultSchema["Tables"] & DefaultSchema["Views"])[DefaultSchemaTableNameOrOptions] extends {
        Row: infer R;
      }
      ? R
      : never
    : never;

export type TablesInsert<
  DefaultSchemaTableNameOrOptions extends
    | keyof DefaultSchema["Tables"]
    | { schema: keyof DatabaseWithoutInternals },
  TableName extends (DefaultSchemaTableNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals;
  }
    ? keyof DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"]
    : never) = never,
> = DefaultSchemaTableNameOrOptions extends { schema: keyof DatabaseWithoutInternals }
  ? DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"][TableName] extends {
      Insert: infer I;
    }
    ? I
    : never
  : DefaultSchemaTableNameOrOptions extends keyof DefaultSchema["Tables"]
    ? DefaultSchema["Tables"][DefaultSchemaTableNameOrOptions] extends {
        Insert: infer I;
      }
      ? I
      : never
    : never;

export type TablesUpdate<
  DefaultSchemaTableNameOrOptions extends
    | keyof DefaultSchema["Tables"]
    | { schema: keyof DatabaseWithoutInternals },
  TableName extends (DefaultSchemaTableNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals;
  }
    ? keyof DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"]
    : never) = never,
> = DefaultSchemaTableNameOrOptions extends { schema: keyof DatabaseWithoutInternals }
  ? DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"][TableName] extends {
      Update: infer U;
    }
    ? U
    : never
  : DefaultSchemaTableNameOrOptions extends keyof DefaultSchema["Tables"]
    ? DefaultSchema["Tables"][DefaultSchemaTableNameOrOptions] extends {
        Update: infer U;
      }
      ? U
      : never
    : never;

export type Enums<
  DefaultSchemaEnumNameOrOptions extends
    | keyof DefaultSchema["Enums"]
    | { schema: keyof DatabaseWithoutInternals },
  EnumName extends (DefaultSchemaEnumNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals;
  }
    ? keyof DatabaseWithoutInternals[DefaultSchemaEnumNameOrOptions["schema"]]["Enums"]
    : never) = never,
> = DefaultSchemaEnumNameOrOptions extends { schema: keyof DatabaseWithoutInternals }
  ? DatabaseWithoutInternals[DefaultSchemaEnumNameOrOptions["schema"]]["Enums"][EnumName]
  : DefaultSchemaEnumNameOrOptions extends keyof DefaultSchema["Enums"]
    ? DefaultSchema["Enums"][DefaultSchemaEnumNameOrOptions]
    : never;

export type CompositeTypes<
  PublicCompositeTypeNameOrOptions extends
    | keyof DefaultSchema["CompositeTypes"]
    | { schema: keyof DatabaseWithoutInternals },
  CompositeTypeName extends (PublicCompositeTypeNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals;
  }
    ? keyof DatabaseWithoutInternals[PublicCompositeTypeNameOrOptions["schema"]]["CompositeTypes"]
    : never) = never,
> = PublicCompositeTypeNameOrOptions extends { schema: keyof DatabaseWithoutInternals }
  ? DatabaseWithoutInternals[PublicCompositeTypeNameOrOptions["schema"]]["CompositeTypes"][CompositeTypeName]
  : PublicCompositeTypeNameOrOptions extends keyof DefaultSchema["CompositeTypes"]
    ? DefaultSchema["CompositeTypes"][PublicCompositeTypeNameOrOptions]
    : never;

export const Constants = {
  public: {
    Enums: {
      statement_period: ["Q1", "Q2", "Q3", "Q4", "FY", "TTM"],
    },
  },
} as const;
