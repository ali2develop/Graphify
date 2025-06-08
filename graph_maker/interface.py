from django.shortcuts import render
from django.http import HttpResponse
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import io
import base64

# Home page view
def home(request):
    return render(request, 'home.html')

# Handle file upload and graph generation
def u_input(request):
    if request.method == "POST":
        file = request.FILES.get("file")
        graph_type = request.POST.get("graph")

        if not file:
            return HttpResponse("No file uploaded", status=400)

        # Optional: restrict large files
        if file.size > 5 * 1024 * 1024:  # 5MB max
            return HttpResponse("File too large", status=400)

        try:
            # Read uploaded CSV or Excel file into DataFrame
            if file.name.endswith('.csv'):
                df = pd.read_csv(file)
            elif file.name.endswith(('.xls', '.xlsx')):
                df = pd.read_excel(file)
            else:
                return HttpResponse("Invalid file format", status=400)

            # Generate and encode the graph
            graph_url = generate_graph(df, graph_type)

            if not graph_url:
                return HttpResponse("Unable to generate the selected graph with the provided data.", status=400)

            return render(request, 'result.html', {'graph': graph_url})

        except Exception as e:
            return HttpResponse(f"Error processing file: {str(e)}", status=500)

    return render(request, 'input.html')


# Generate a graph image from the DataFrame based on the selected type
def generate_graph(df, graph_type):
    plt.figure(figsize=(8, 6))
    sns.set_style("darkgrid")

    try:
        if graph_type == 'hist':
            df.hist(bins=10, edgecolor='black', alpha=0.7)
            plt.xticks(rotation=45)

        elif graph_type == 'scatter' and len(df.columns) >= 2:
            sns.scatterplot(x=df.columns[0], y=df.columns[1], data=df)
            plt.xticks(rotation=45)

        elif graph_type == 'line':
            df.plot(kind='line')
            plt.xticks(rotation=45)

        elif graph_type == 'box' and len(df.columns) >= 2:
            sns.boxplot(data=df)
            plt.xticks(rotation=45)

        elif graph_type == 'pie' and len(df.columns) >= 1:
            column_name = df.columns[0]
            counts = df[column_name].value_counts()
            if counts.nunique() > 20:
                counts = counts.nlargest(10)
            plt.figure(figsize=(8, 8))
            counts.plot(kind='pie', autopct='%1.1f%%', startangle=90, cmap='Set2',
                        textprops={'fontsize': 12},
                        wedgeprops={'edgecolor': 'black', 'linewidth': 1})
            plt.ylabel('')
            plt.title(f"Distribution of {column_name}")

        elif graph_type == 'bar' and len(df.columns) >= 2:
            sns.barplot(x=df.columns[0], y=df.columns[1], data=df)
            plt.xticks(rotation=45)
            plt.title(f"Bar chart of {df.columns[1]} by {df.columns[0]}")

        elif graph_type == 'heatmap':
            corr = df.select_dtypes(include='number').corr()
            sns.heatmap(corr, annot=True, cmap='coolwarm', fmt=".2f")
            plt.title("Correlation Heatmap")

        elif graph_type == 'area':
            df.select_dtypes(include='number').plot(kind='area', stacked=False, alpha=0.5)
            plt.xticks(rotation=45)
            plt.title("Area Chart")

        elif graph_type == 'violin':
            numeric_df = df.select_dtypes(include='number')
            if numeric_df.shape[1] >= 2:
                melted_df = numeric_df.melt(var_name='Variable', value_name='Value')
                sns.violinplot(x='Variable', y='Value', data=melted_df)
            else:
                return None

        elif graph_type == 'kde':
            numeric_df = df.select_dtypes(include='number')
            if numeric_df.shape[1] >= 1:
                for col in numeric_df.columns:
                    sns.kdeplot(numeric_df[col], label=col, fill=True)
                plt.legend()
                plt.title("KDE Plot")
            else:
                return None

        elif graph_type == 'pairplot':
            numeric_df = df.select_dtypes(include='number')
            if numeric_df.shape[1] >= 2:
                pair = sns.pairplot(numeric_df)
                buffer = io.BytesIO()
                pair.fig.savefig(buffer, format='png')
                buffer.seek(0)
                return f'data:image/png;base64,{base64.b64encode(buffer.getvalue()).decode()}'
            else:
                return None

        # For all other plots except pairplot (which already returns above)
        plt.tight_layout()
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', bbox_inches='tight')
        buffer.seek(0)
        image_png = buffer.getvalue()
        buffer.close()

        graph_url = base64.b64encode(image_png).decode('utf-8')
        return f'data:image/png;base64,{graph_url}'

    except Exception as e:
        print(f"Error generating graph: {e}")
        return None
