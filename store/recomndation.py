import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from django.core.cache import cache
from .models import Product


def get_product_dataframe():
    products = Product.objects.filter(is_available=True)

    data = []

    for p in products:
        data.append({
            "id": p.id,
            "product_name": p.product_name,
            "category": str(p.category),
            "subcategory": str(p.subcategory),
            "description": p.description if p.description else ""
        })

    df = pd.DataFrame(data)

    if df.empty:
        return df

    df["content"] = (
        df["product_name"] + " " +
        df["category"] + " " +
        df["subcategory"] + " " +
        df["description"]
    )

    return df


def get_recommendations(product_id, num=8):

    cache_key = f"rec_{product_id}"
    cached = cache.get(cache_key)

    if cached:
        return cached

    df = get_product_dataframe()

    if df.empty:
        return Product.objects.none()

    tfidf = TfidfVectorizer(stop_words="english")
    tfidf_matrix = tfidf.fit_transform(df["content"])

    cosine_sim = cosine_similarity(tfidf_matrix, tfidf_matrix)

    ## Find index of given product
    index = df[df["id"] == product_id].index

    if len(index) == 0:
        return Product.objects.none()

    index = index[0]
    # Fetch similer list
    sim_scores = list(enumerate(cosine_sim[index]))
    sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)

    ### Skip same product
    sim_scores = sim_scores[1:num+1]

    ## Takse Id's of the products
    product_indices = [i[0] for i in sim_scores]
    recommended_ids = df.iloc[product_indices]["id"].values
    
    ## Get real products from database
    recommendations = Product.objects.filter(id__in=recommended_ids, is_available=True)
    cache.set(cache_key, recommendations, 60 * 60)

    return recommendations
