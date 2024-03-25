use rand::prelude::*;
use std::time::Instant;
use tfhe::prelude::*;
use tfhe::{
    generate_keys, 
    set_server_key, 
    ConfigBuilder, 
    FheBool,
    FheUint,
    FheUint32, 
    FheUint32Id, 
};


fn filtered_sum(data: Vec<Vec<FheUint<FheUint32Id>>>, filters: &str, filter_values: Vec<FheUint<FheUint32Id>>, zero: FheUint<FheUint32Id>) -> FheUint<FheUint32Id> {
    // assume that the first column in data is to be aggregated

    println!("Data size: {}, {}", data.len(), data[0].len());
    println!("filters: {}", filters);

    // initialize M
    let n = data.len();
    let m = data[0].len();
    assert!(m == filters.len() + 1);
    assert!(m == filter_values.len() + 1);

    let mut aggregate: Vec<FheUint<FheUint32Id>> = vec![];

    for i in 0..n {
        if i % 10 == 0 {
            println!("Filtering row number {}/{}", i, n);
        }

        let f = filters.chars().nth(0).unwrap();
        let mut include: FheBool = match f {
            '<' => data[i][1].lt(&filter_values[0]),
            '>' => data[i][1].gt(&filter_values[0]),
            '=' => data[i][1].eq(&filter_values[0]),
            _ => panic!("invalid filter char"),
        };
        for j in 2..m {
            let f = filters.chars().nth(j-1).unwrap();
            include = include & match f {
                '<' => data[i][j].lt(&filter_values[j-1]),
                '>' => data[i][j].gt(&filter_values[j-1]),
                '=' => data[i][j].eq(&filter_values[j-1]),
                _ => panic!("invalid filter char"),
            };
        }

        aggregate.push(include.if_then_else(&data[i][0], &zero));
    }

    let mut total = zero;
    for (i, x) in aggregate.iter().enumerate() {
        if i == 0 {
            continue;
        }

        total += x;
    }

    return total;
}


fn main() {
    let n: usize = 20;
    let m: usize = 2;

    let config = ConfigBuilder::default().build();
    let (client_key, server_key) = generate_keys(config);
    
    // generate data and filters
    let t1 = Instant::now();
    println!("Starting data generation");
    let mut data: Vec<Vec<FheUint32>> = vec![];
    for _ in 0..n {
        data.push(
            (0..m).map(|_| FheUint32::encrypt(random::<u32>(), &client_key)).collect()
        );
    }

    let filter_values = (0..(m-1)).map(|_| FheUint32::encrypt(random::<u32>(), &client_key)).collect();
    let zero = FheUint32::encrypt(0u32, &client_key);

    set_server_key(server_key);

    let t2 = Instant::now();
    println!("Starting filtered sum");
    let answer = filtered_sum(data, "<", filter_values, zero);
    println!("Finished filtered sum");

    let decrypted_answer: u32 = answer.decrypt(&client_key);

    println!("Filtered sum answer: {}", decrypted_answer);
    println!("Data generation duration: {} ms", t1.elapsed().as_millis());
    println!("Filtered sum duration:    {} ms", t2.elapsed().as_millis());
}
