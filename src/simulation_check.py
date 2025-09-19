import ast


class SimulationExecutionCheck:

    def __init__(self):
        pass

    def factory_level_check(self, df):
        # Check if values are null
        null_values = df.isnull().sum().sum()
        if null_values > 0:
            return f"{null_values} Null values are present in the data"
        # Check if values are duplicate
        duplicate_values = df.loc[
            df["Factory"].duplicated(keep="first"), "Factory"
        ].to_list()
        if len(duplicate_values) > 0:
            return f"Factory values '{', '.join(duplicate_values)}' are duplicated"
        # Check if values are appropriate
        for col in ["Factory"]:
            try:
                df[col] = df[col].astype(str)
            except Exception as e:
                return f"Factory Level: '{col}' column - {e}"
        for col in ["Holding Cost Per Unit Per Day"]:
            try:
                df[col] = df[col].astype(float)
            except Exception as e:
                return f"Factory Level: '{col}' column - {e}"
        return "Passed"

    def warehouse_level_check(self, df):
        # Check if values are null
        null_values = df.isnull().sum().sum()
        if null_values > 0:
            return f"{null_values} Null values are present in the data"
        # Check if values are duplicate
        duplicate_values = df.loc[
            df["Warehouse"].duplicated(keep="first"), "Warehouse"
        ].to_list()
        if len(duplicate_values) > 0:
            return f"Warehouse values '{', '.join(duplicate_values)}' are duplicated"
        # Check if values are appropriate
        for col in ["Warehouse"]:
            try:
                df[col] = df[col].astype(str)
            except Exception as e:
                return f"Warehouse Level: '{col}' column - {e}"
        for col in ["Holding Cost Per Unit Per Day"]:
            try:
                df[col] = df[col].astype(float)
            except Exception as e:
                return f"Warehouse Level: '{col}' column - {e}"
        return "Passed"

    def factory_product_level_check(self, df, factory_level_df):
        # Check if values are null
        null_values = df.isnull().sum().sum()
        if null_values > 0:
            return f"{null_values} Null values are present in the data"
        # Check if values are duplicate
        duplicate_values = (
            df.loc[
                df[["Factory", "Product"]].duplicated(keep="first"),
                ["Factory", "Product"],
            ]
            .astype(str)
            .values
        )
        if len(duplicate_values) > 0:
            return f"Factory-Product values '{', '.join(['-'.join(i) for i in duplicate_values])}' are duplicated"

        # Check if factory are present
        factory_list = factory_level_df["Factory"].unique()
        not_available = []
        for i in df["Factory"].unique():
            if i not in factory_list:
                not_available.append(i)
        if len(not_available) > 0:
            if len(not_available) == 1:
                return f"Data for factory '{', '.join(not_available)}' is not available in Factory Level data"
            else:
                return f"Data for factories '{', '.join(not_available)}' are not available in Factory Level data"

        # Check for duplicate products
        duplicate_products = list(
            df.loc[df["Product"].duplicated(), "Product"].unique()
        )
        if len(duplicate_products) > 0:
            return f"Duplicates product(s) '{', '.join(duplicate_products)}' in Factory Product Level data"

        # Check if values are appropriate
        for col in ["Factory", "Product"]:
            try:
                df[col] = df[col].astype(str)
            except Exception as e:
                return f"Factory Product Level: '{col}' column - {e}"
        for col in [
            "Production Capacity",
            "Starting Inventory",
            "Production Cost Per Unit",
        ]:
            try:
                df[col] = df[col].astype(float)
            except Exception as e:
                return f"Factory Product Level: '{col}' column - {e}"

        return "Passed"

    def warehouse_factory_level_check(
        self, df, warehouse_level_df, factory_level_df, factory_product_level_df
    ):
        # Check if values are null
        null_values = df.isnull().sum().sum()
        if null_values > 0:
            return f"{null_values} Null values are present in the data"

        # Check if values are duplicate
        duplicate_values = (
            df.loc[
                df[["Warehouse", "Factory"]].duplicated(keep="first"),
                ["Warehouse", "Factory"],
            ]
            .astype(str)
            .values
        )
        if len(duplicate_values) > 0:
            return f"Warehouse-Factory values '{', '.join(['-'.join(i) for i in duplicate_values])}' are duplicated"

        # Check if warehouse is present
        warehouse_list = warehouse_level_df["Warehouse"].unique()
        not_available = []
        for i in df["Warehouse"].unique():
            if i not in warehouse_list:
                not_available.append(i)
        if len(not_available) > 0:
            if len(not_available) == 1:
                return f"Data for warehouse '{', '.join(not_available)}' is not available in Warehouse Level data"
            else:
                return f"Data for warehouses '{', '.join(not_available)}' are not available in Warehouse Level data"

        # Check if factory is present
        factory_list = factory_level_df["Factory"].unique()
        not_available = []
        for i in df["Factory"].unique():
            if i not in factory_list:
                not_available.append(i)
        if len(not_available) > 0:
            if len(not_available) == 1:
                return f"Data for factory '{', '.join(not_available)}' is not available in Factory Level data"
            else:
                return f"Data for factories '{', '.join(not_available)}' are not available in Factory Level data"

        # Check if values are appropriate
        for col in ["Warehouse", "Factory", "Lead Time Distribution"]:
            try:
                df[col] = df[col].astype(str)
            except Exception as e:
                return f"Warehouse Factory Level: '{col}' column - {e}"
        for col in [
            "Transporatation Cost Per Unit Per Km",
            "Distance Between Warehouse & Factory",
        ]:
            try:
                df[col] = df[col].astype(float)
            except Exception as e:
                return f"Warehouse Factory Level: '{col}' column - {e}"
        # Check if value is appropriate
        for _, row in df.iterrows():
            message = self.check_parameters_for_distribution(
                row["Lead Time Parameters"],
                row["Lead Time Distribution"],
                "Lead Time Parameters",
            )
            if message is not None:
                return f"Warehouse Factory Level: {message}"
        return "Passed"

    def warehouse_product_level_check(
        self,
        df,
        warehouse_level_df,
        factory_product_level_df,
        warehouse_factory_level_df,
    ):
        # Check if values are null
        null_values = df.isnull().sum().sum()
        if null_values > 0:
            return f"{null_values} Null values are present in the data"

        # Check if values are duplicate
        duplicate_values = (
            df.loc[
                df[["Warehouse", "Product"]].duplicated(keep="first"),
                ["Warehouse", "Product"],
            ]
            .astype(str)
            .values
        )
        if len(duplicate_values) > 0:
            return f"Warehouse-Product values '{', '.join(['-'.join(i) for i in duplicate_values])}' are duplicated"

        # Check if warehouse is present in the warehouse data
        warehouse_list = warehouse_level_df["Warehouse"].unique()
        not_available = []
        for i in df["Warehouse"].unique():
            if i not in warehouse_list:
                not_available.append(i)
        if len(not_available) > 0:
            if len(not_available) == 1:
                return f"Data for warehouse '{', '.join(not_available)}' is not available in Warehouse Level data"
            else:
                return f"Data for warehouses '{', '.join(not_available)}' are not available in Warehouse Level data"

        # Check if product is present in factory product
        product_list = factory_product_level_df["Product"].unique()
        not_available = []
        for i in df["Product"].unique():
            if i not in product_list:
                not_available.append(i)
        if len(not_available) > 0:
            if len(not_available) == 1:
                return f"Data for product '{', '.join(not_available)}' is not available in Factory Product Level data"
            else:
                return f"Data for products '{', '.join(not_available)}' are not available in Factory Product Level data"

        # Iterate through each row
        # Check for each warehouse product, what all factories produce that product and whether distance between that factory and warehouse is available
        # Atleast one factory-warehouse combination must be available for a product
        available_warehouse_factory_combination = warehouse_factory_level_df[
            ["Warehouse", "Factory"]
        ].values.tolist()
        for _, row in df.iterrows():
            factory_list = factory_product_level_df.loc[
                factory_product_level_df["Product"] == row["Product"], "Factory"
            ].to_list()
            warehouse_factory_combination = [
                [row["Warehouse"], i] for i in factory_list
            ]
            available_atleast_one = []
            for i in warehouse_factory_combination:
                if i in available_warehouse_factory_combination:
                    available_atleast_one.append(i)
            if len(available_atleast_one) == 0:
                if len(factory_list) == 0:
                    return f"For Warehouse '{row['Warehouse']}' & Product '{row['Product']}', data is not available in Warehouse Factory Level. No factories available for Product '{row['Product']}'"
                elif len(factory_list) == 1:
                    return f"For Warehouse '{row['Warehouse']}' & Product '{row['Product']}', data is not available in Warehouse Factory Level. Available factory for Product '{row['Product']}' is {factory_list[0]}"
                else:
                    return f"For Warehouse '{row['Warehouse']}' & Product '{row['Product']}', data is not available in Warehouse Factory Level. Available factories for Product '{row['Product']}' are {', '.join(factory_list)}"

        # Check if values are appropriate
        for col in [
            "Warehouse",
            "Product",
            "Daily Demand Distribution",
            "Inventory Policy",
        ]:
            try:
                df[col] = df[col].astype(str)
            except Exception as e:
                return f"Warehouse Product Level: '{col}' column - {e}"
        for col in ["Safety Stock", "Starting Inventory", "Opportunity Cost Per Unit"]:
            try:
                df[col] = df[col].astype(float)
            except Exception as e:
                return f"Warehouse Product Level: '{col}' column - {e}"
        for _, row in df.iterrows():
            message = self.check_parameters_for_distribution(
                row["Demand Distribution Parameters"],
                row["Daily Demand Distribution"],
                "Demand Distribution Parameters",
            )
            if message is not None:
                return f"Warehouse Product Level: {message}"
        for _, row in df.iterrows():
            if row["Inventory Policy"] == "Min/Max":
                message = self.check_parameters_for_min_max_inventory_policy(
                    row["Inventory Policy Parameters"],
                    "Inventory Policy Parameters",
                )
                if message is not None:
                    return f"Warehouse Product Level: {message}"
            else:
                return f"Warehouse Product Level:  Invalid inventory policy '{row['Inventory Policy']}, Available inventory policy - Min/Max"
        return "Passed"

    def check_parameters_for_distribution(
        self, value_string_dict, distribution, column_name
    ):

        # value_string_dict -> Dictionary with key as parameters and value as parameter values of distribution
        # distribution -> Normal, Exponential, Categorical
        # column_name -> Column which value belongs to
        # Assuming all parameters available
        message = None
        try:
            # Extract dictionary
            value = ast.literal_eval(value_string_dict)
            # Normal distribution
            if distribution == "Normal":
                # Check mean
                if "mean" not in value:
                    message = f"For column '{column_name}', value '{value_string_dict}' is invalid. 'mean' key is not present"
                    return message

                else:
                    # Check if value is float
                    try:
                        mean_float = float(value["mean"])
                    except:
                        message = f"For column '{column_name}', value '{value_string_dict}' is invalid. 'mean' value is invalid, it must be float"
                        return message
                # Check std dev
                if "std_dev" not in value:
                    message = f"For column '{column_name}', value '{value_string_dict}' is invalid. 'std_dev' key is not present"
                    return message
                else:
                    # Check if value is float
                    try:
                        std_dev_float = float(value["std_dev"])
                    except:
                        message = f"For column '{column_name}', value '{value_string_dict}' is invalid. 'std_dev' value is invalid, it must be float"
                        return message
            # Exponential
            elif distribution == "Exponential":
                if "lambda" not in value:
                    message = f"For column '{column_name}', value '{value_string_dict}' is invalid. 'lambda' key is not present"
                    return message
                else:
                    # Check if value is float
                    try:
                        lambda_float = float(value["lambda"])
                    except:
                        message = f"For column '{column_name}', value '{value_string_dict}' is invalid. 'lambda' value is invalid, it must be float"
                        return message
                    # All parameters available
                    return message
            # Categorical
            elif distribution == "Categorical":
                for k in value:
                    try:
                        key_int = int(k)
                    except:
                        message = f"For column '{column_name}', value '{value_string_dict}' is invalid. 'lead_time' key is invalid, it must be integer"
                        return message
                    try:
                        value_int = float(value[k])
                    except:
                        message = f"For column '{column_name}', value '{value_string_dict}' is invalid. 'lead_time' value is invalid, it must be float"
                        return message
                # Check if sum of probability score is 1
                if round(sum(value.values()), 2) != 1:
                    message = f"For column '{column_name}', value '{value_string_dict}' is invalid. The sum of probability '{round(sum(value.values()), 2)}' is not equal to 1"
                    return message
        except:
            # Message for Normal distribution
            if distribution == "Normal":
                message = (
                    f"For column '{column_name}', value '{value_string_dict}' is invalid. "
                    + "For normal distribution provide in following json format: {'mean': mean_value, 'std_dev': std_dev_value}. The mean_value & std_dev_value must be float"
                )
            elif distribution == "Exponential":
                message = (
                    f"For column '{column_name}', value '{value_string_dict}' is invalid. "
                    + "For exponential distribution provide in following json format: {'lambda': lambda_value}. The lambda_value must be float"
                )
            elif distribution == "Categorical":
                message = (
                    f"For column '{column_name}', value '{value_string_dict}' is invalid. "
                    + "For categorical distribution provide in following json format: {lead_time_1 : probability_score, lead_time_2 : probability_score, ...}. Lead time must be integer & probability score must be float. The sum of probability must be 1"
                )
        return message

    def check_parameters_for_min_max_inventory_policy(
        self, value_string_dict, column_name
    ):
        # value_string_dict -> Dictionary with key as parameters (min/max) and value as parameter values
        message = None
        try:
            # Extract dictionary
            value = ast.literal_eval(value_string_dict)
            # Check min value
            if "min" not in value:
                message = f"For column '{column_name}', value '{value_string_dict}' is invalid. 'min' key is not present"
                return message

            else:
                # Check if value is int
                try:
                    min_int = int(value["min"])
                except:
                    message = f"For column '{column_name}', value '{value_string_dict}' is invalid. 'min' value is invalid, it must be integer"
                    return message
            # Check max value
            if "max" not in value:
                message = f"For column '{column_name}', value '{value_string_dict}' is invalid. 'max' key is not present"
                return message

            else:
                # Check if value is int
                try:
                    max_int = int(value["max"])
                except:
                    message = f"For column '{column_name}', value '{value_string_dict}' is invalid. 'max' value is invalid, it must be integer"
                    return message
            # Check if max is less than min
            if max_int < min_int:
                message = f"For column '{column_name}', max value '{max_int}' is less than min value '{min_int}'. 'max' value must be greater than or equal to 'min' value"
                return message
        except:
            message = (
                f"For column '{column_name}', value '{value_string_dict}' is invalid. "
                + "For min/max inventory policy provide in following json format: {'min': min_value, 'max': max_value}. The min_value & max_value must be integer"
            )
        return message
